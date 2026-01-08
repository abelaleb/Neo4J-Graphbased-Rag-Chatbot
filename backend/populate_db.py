import os
import requests
import time
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Load environment variables (prefer values from .env over existing ones)
load_dotenv(override=True)

# --- Configuration ---
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
BALLDONTLIE_API_KEY = os.getenv("BALLDONTLIE_API_KEY") # Optional: Get free key from balldontlie.io for better limits

# API Endpoints
API_URL = "https://api.balldontlie.io/v1"
HEADERS = {"Authorization": BALLDONTLIE_API_KEY} if BALLDONTLIE_API_KEY else {}

class NBAGraphLoader:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

    def close(self):
        self.driver.close()

    def setup_schema(self):
        """Creates indexes to ensure data integrity and faster queries."""
        print("Creating indexes...")
        with self.driver.session() as session:
            # Create unique constraints for Players and Teams
            session.run("CREATE CONSTRAINT player_id_unique IF NOT EXISTS FOR (p:Player) REQUIRE p.id IS UNIQUE")
            session.run("CREATE CONSTRAINT team_id_unique IF NOT EXISTS FOR (t:Team) REQUIRE t.id IS UNIQUE")
            # Create fulltext index for fuzzy search (helps the LLM match names)
            try:
                session.run("CREATE FULLTEXT INDEX playerNames IF NOT EXISTS FOR (n:Player) ON EACH [n.name]")
            except:
                pass # Index might already exist
        print("Schema setup complete.")

    def fetch_teams(self):
        """Fetches all 30 NBA teams."""
        print("Fetching teams...")
        try:
            response = requests.get(f"{API_URL}/teams", headers=HEADERS)
            if response.status_code == 200:
                return response.json()['data']
            else:
                print(f"Error fetching teams: {response.status_code}")
                return []
        except Exception as e:
            print(f"Connection error: {e}")
            return []

    def load_teams(self, teams):
        """Loads teams into Neo4j."""
        query = """
        UNWIND $teams AS team_data
        MERGE (t:Team {id: team_data.id})
        SET t.name = team_data.full_name,
            t.abbreviation = team_data.abbreviation,
            t.city = team_data.city,
            t.conference = team_data.conference,
            t.division = team_data.division
        """
        with self.driver.session() as session:
            session.run(query, teams=teams)
        print(f"Successfully loaded {len(teams)} teams.")

    def fetch_active_players(self):
        """Fetches active players page by page."""
        print("Fetching active players (this may take a moment)...")
        all_players = []
        page = 1
        while True:
            # Only fetch active players per page to save time
            url = f"{API_URL}/players?per_page=100&page={page}"
            try:
                response = requests.get(url, headers=HEADERS)
                if response.status_code != 200:
                    break
                
                data = response.json()
                players = data['data']
                
                if not players:
                    break
                
                # Filter for active players only if API supports it, otherwise logic handles it
                # We simply append all fetched players
                all_players.extend(players)
                
                print(f"Fetched page {page}...")
                page += 1
                
                # Rate limit safety (free tier is 30 req/min)
                if not BALLDONTLIE_API_KEY:
                    time.sleep(2) 

                # Safety break for testing (remove this to fetch ALL thousands of players)
                if page > 10: 
                    print("Stopping at 10 pages for demo purposes. Remove limit in code to fetch all.")
                    break

            except Exception as e:
                print(f"Error fetching players: {e}")
                break
        
        return all_players

    def load_players(self, players):
        """Loads players and connects them to their teams."""
        # Cypher query to create Player and relationship to Team
        query = """
        UNWIND $players AS p
        MERGE (player:Player {id: p.id})
        SET player.name = p.first_name + ' ' + p.last_name,
            player.first_name = p.first_name,
            player.last_name = p.last_name,
            player.position = p.position,
            player.height = CASE WHEN p.height_feet IS NOT NULL THEN p.height_feet + "'" + p.height_inches + '"' ELSE null END,
            player.weight = p.weight_pounds,
            player.jersey_number = p.jersey_number

        WITH player, p
        WHERE p.team IS NOT NULL
        MATCH (t:Team {id: p.team.id})
        MERGE (player)-[:PLAYS_FOR]->(t)
        """
        
        # Batch processing to prevent memory overload
        batch_size = 500
        with self.driver.session() as session:
            for i in range(0, len(players), batch_size):
                batch = players[i:i+batch_size]
                session.run(query, players=batch)
                print(f"Processed batch {i} to {i+len(batch)}")
        
        print(f"Successfully loaded {len(players)} players.")

if __name__ == "__main__":
    loader = NBAGraphLoader()
    try:
        loader.setup_schema()
        
        # 1. Load Teams
        teams = loader.fetch_teams()
        if teams:
            loader.load_teams(teams)
        
        # 2. Load Players
        players = loader.fetch_active_players()
        if players:
            loader.load_players(players)
            
    finally:
        loader.close()
        print("Database population finished.")
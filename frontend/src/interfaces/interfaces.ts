export interface message {
    content: string;
    role: "user" | "assistant";
    id: string;
    /*eslint-disable-next-line @typescript-eslint/no-explicit-any*/
    intermediate_steps?: any[];
}
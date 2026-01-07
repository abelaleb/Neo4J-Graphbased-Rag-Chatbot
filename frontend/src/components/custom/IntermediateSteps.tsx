import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CodeBlock } from "./CodeBlock";

interface Step {
    action: {
        tool: string;
        tool_input: string;
        log: string;
    };
    observation: any;
}

interface IntermediateStepsProps {
    steps: Step[];
    finalAnswer: string;
}

export function IntermediateSteps({ steps, finalAnswer }: IntermediateStepsProps) {
    if (!steps || steps.length === 0) {
        return null;
    }

    const renderObservation = (observation: any) => {
        if (typeof observation === 'string') {
            return <p className="text-sm text-muted-foreground">{observation}</p>;
        }

        if (observation.intermediate_steps) {
            return (
                <div className="space-y-2">
                    {observation.intermediate_steps.map((subStep: any, index: number) => (
                        <div key={index}>
                            {subStep.query && (
                                <>
                                    <p className="font-semibold text-sm">Generated Query:</p>
                                    <CodeBlock language="cypher" value={subStep.query.replace("cypher\n", "")} />
                                </>
                            )}
                            {subStep.context && (
                                <>
                                    <p className="font-semibold text-sm mt-2">Query Result:</p>
                                    <CodeBlock language="json" value={JSON.stringify(subStep.context, null, 2)} />
                                </>
                            )}
                        </div>
                    ))}
                     <p className="font-semibold text-sm mt-2">Tool Result:</p>
                     <p className="text-sm text-muted-foreground">{observation.result}</p>
                </div>
            );
        }
        
        return <CodeBlock language="json" value={JSON.stringify(observation, null, 2)} />;
    };

    return (
        <div className="space-y-4 mt-4">
            <h3 className="font-semibold">Intermediate Steps</h3>
            {steps.map((step, index) => (
                <Card key={index} className="bg-background/50">
                    <CardHeader className="p-4">
                        <CardTitle className="text-base">Step {index + 1}: Using Tool `{step.action.tool}`</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4 p-4 pt-0">
                        <div>
                            <p className="font-semibold text-sm">Tool Input:</p>
                            <div className="text-sm text-muted-foreground p-2 bg-secondary rounded-md mt-1">
                                <pre className="whitespace-pre-wrap font-sans">{step.action.tool_input}</pre>
                            </div>
                        </div>
                        <div>
                            <p className="font-semibold text-sm">Observation:</p>
                            <div className="p-2 bg-secondary rounded-md mt-1">
                                {renderObservation(step.observation)}
                            </div>
                        </div>
                    </CardContent>
                </Card>
            ))}
            {steps.length > 1 && (
                 <Card key={steps.length} className="bg-background/50">
                    <CardHeader className="p-4">
                        <CardTitle className="text-base">Step {steps.length + 1}: Formulating Response from Agentic Trace</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4 p-4 pt-0">
                        <div>
                            <p className="font-semibold text-sm">Observation:</p>
                            <div className="p-2 bg-secondary rounded-md mt-1">
                                <p className="text-sm text-muted-foreground">{finalAnswer}</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            )}
        </div>
    );
}
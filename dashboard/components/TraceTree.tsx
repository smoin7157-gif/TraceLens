type SpanNode = {
  id: string;
  name: string;
  kind: string;
  children?: SpanNode[];
};

export function TraceTree({ nodes }: { nodes: SpanNode[] }) {
  return (
    <ul className="space-y-2 text-sm">
      {nodes.map((node) => (
        <li key={node.id} className="rounded border border-slate-700 bg-slate-900/60 p-2">
          <div className="font-medium text-slate-100">
            {node.name} <span className="text-slate-400">({node.kind})</span>
          </div>
          {node.children && node.children.length > 0 && (
            <div className="ml-4 mt-2 border-l border-slate-700 pl-3">
              <TraceTree nodes={node.children} />
            </div>
          )}
        </li>
      ))}
    </ul>
  );
}
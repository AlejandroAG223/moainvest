export function BackendOffline() {
  return (
    <div role="alert" className="rounded-2xl border border-dashed border-line bg-mist p-8">
      <p className="text-lg font-semibold">No pudimos conectar con el servicio de datos.</p>
      <p className="mt-2 text-muted">
        Asegúrate de que el backend de Flask esté en marcha (<code className="font-mono text-sm">uv run run.py</code>) y vuelve a cargar la página.
      </p>
    </div>
  );
}

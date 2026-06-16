export function Spinner({ size = "md", className = "" }) {
  const sz = { sm: "h-4 w-4 border-2", md: "h-6 w-6 border-2", lg: "h-10 w-10 border-[3px]" }[size];
  return (
    <div className={`animate-spin rounded-full border-gray-200 border-t-indigo-600 ${sz} ${className}`} />
  );
}

export function PageLoader({ message = "Loading…" }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 gap-3">
      <Spinner size="lg" />
      <p className="text-sm text-gray-400">{message}</p>
    </div>
  );
}

import { cn } from "@/lib/utils/cn";

interface CardProps {
  className?: string;
  children: React.ReactNode;
}

export function Card({ className, children }: CardProps) {
  return (
    <div
      className={cn(
        "bg-white rounded-lg shadow-md border border-gray-200",
        className
      )}
    >
      {children}
    </div>
  );
}

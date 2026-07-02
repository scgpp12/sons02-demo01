import type { ReactNode } from "react";

import { Label } from "@/components/ui/label";

interface Props {
  label: string;
  children: ReactNode;
  required?: boolean;
  className?: string;
}

export function Field({ label, children, required, className }: Props) {
  return (
    <div className={className ?? "space-y-1.5"}>
      <Label>
        {label}
        {required && <span className="ml-0.5 text-destructive">*</span>}
      </Label>
      {children}
    </div>
  );
}

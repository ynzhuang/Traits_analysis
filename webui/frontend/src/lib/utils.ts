import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Merge Tailwind class names, resolving conflicts in favour of the last one.
 *
 * The standard shadcn/ui helper — `components.json` points its `utils` alias
 * here, and every component under `components/ui/` imports it.
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

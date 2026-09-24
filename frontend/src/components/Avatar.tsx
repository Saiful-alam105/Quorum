import { cn } from "@/lib/utils"

type AvatarProps = {
  name: string | null | undefined
  src: string | null | undefined
  size?: "sm" | "md"
  className?: string
}

export function Avatar({ name, src, size = "sm", className }: AvatarProps) {
  const initial = (name ?? "?").slice(0, 1).toUpperCase()
  const sizeClass = size === "sm" ? "h-6 w-6 text-xs" : "h-9 w-9 text-sm"

  if (src) {
    return (
      <img
        src={src}
        alt=""
        className={cn("shrink-0 rounded-full object-cover", sizeClass, className)}
      />
    )
  }

  return (
    <span
      className={cn(
        "flex shrink-0 items-center justify-center rounded-full bg-primary/20 font-semibold text-primary",
        sizeClass,
        className,
      )}
    >
      {initial}
    </span>
  )
}
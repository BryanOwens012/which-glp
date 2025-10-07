import { ExternalLink } from "lucide-react"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { RedditReference, getRedditPermalink } from "@/lib/types"

type RedditLinkProps = {
  reference: RedditReference
  className?: string
  showText?: boolean
}

/**
 * Reddit permalink icon that opens in a new tab
 * Shows tooltip on hover with post/comment type
 */
export function RedditLink({ reference, className = "", showText = false }: RedditLinkProps) {
  const permalink = getRedditPermalink(reference)
  const label = reference.type === "post" ? "View Reddit Post" : "View Reddit Comment"

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <a
            href={permalink}
            target="_blank"
            rel="noopener noreferrer"
            className={`inline-flex items-center gap-1 text-muted-foreground hover:text-primary transition-colors ${className}`}
            aria-label={label}
          >
            <ExternalLink className="h-3.5 w-3.5" />
            {showText && <span className="text-xs">Source</span>}
          </a>
        </TooltipTrigger>
        <TooltipContent>
          <p>{label}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}

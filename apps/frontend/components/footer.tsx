import Link from "next/link"

export const Footer = () => {
  return (
    <footer className="border-t border-border/40 bg-background">
      <div className="container mx-auto px-4 py-8">
        {/* Medical Disclaimer */}
        <div className="mb-6 text-center">
          <p className="text-xs text-muted-foreground max-w-4xl mx-auto leading-relaxed">
            WhichGLP is an informational comparison tool only. We are not healthcare providers and do not offer medical advice.
            All data is self-reported by Reddit users and has not been verified by medical professionals.
            Always consult with a qualified healthcare provider before starting, stopping, or changing any medication.
            We are not responsible for any health outcomes resulting from use of this site.
          </p>
        </div>

        {/* Footer Links */}
        <div className="flex flex-col items-center justify-between gap-4 md:flex-row border-t border-border/40 pt-6">
          <div className="text-sm text-muted-foreground">
            © 2025 WhichGLP. All rights reserved.
          </div>
          <div className="flex gap-6">
            <Link
              href="/privacy"
              className="text-sm text-muted-foreground hover:text-foreground"
            >
              Privacy
            </Link>
            <Link
              href="/terms"
              className="text-sm text-muted-foreground hover:text-foreground"
            >
              Terms
            </Link>
            <a
              href="mailto:contact@whichglp.com"
              className="text-sm text-muted-foreground hover:text-foreground"
            >
              Contact
            </a>
          </div>
        </div>
      </div>
    </footer>
  )
}

import Link from "next/link";
import Image from "next/image";

export const Navigation = () => {
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 border-b border-border/40 bg-background/80 backdrop-blur-sm">
      <div className="container mx-auto flex items-center justify-between px-4 py-4">
        <Link href="/compare" className="flex items-center gap-2">
          <Image
            src="/icon.svg"
            alt="WhichGLP Logo"
            width={40}
            height={40}
            className="h-10 w-10"
          />
          <div className="text-2xl font-bold text-foreground">
            Which<span className="text-primary">GLP</span>
          </div>
        </Link>

        <div className="hidden items-center gap-8 md:flex">
          <Link
            href="/compare"
            prefetch={true}
            className="text-sm text-muted-foreground transition-colors hover:text-foreground"
          >
            Compare
          </Link>
          <Link
            href="/experiences"
            prefetch={true}
            className="text-sm text-muted-foreground transition-colors hover:text-foreground"
          >
            Experiences
          </Link>
          {/* <Link
            href="/dashboard"
            className="text-sm text-muted-foreground transition-colors hover:text-foreground"
          >
            Dashboard
          </Link> */}
          <Link
            href="/recommendations"
            prefetch={true}
            className="text-sm text-muted-foreground transition-colors hover:text-foreground"
          >
            Recommend for Me
          </Link>
          <Link
            href="/about"
            prefetch={true}
            className="text-sm text-muted-foreground transition-colors hover:text-foreground"
          >
            About
          </Link>
        </div>
      </div>
    </nav>
  );
}

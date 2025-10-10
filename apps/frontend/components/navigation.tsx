"use client";

import Link from "next/link";
import Image from "next/image";
import { useState } from "react";
import { Menu } from "lucide-react";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";

export const Navigation = () => {
  const [open, setOpen] = useState(false);

  const navLinks = [
    { href: "/compare", label: "Compare" },
    { href: "/experiences", label: "Experiences" },
    { href: "/recommendations", label: "Recommend for Me (AI)" },
    { href: "/about", label: "About" },
  ];

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 border-b border-border/40 bg-background/80 backdrop-blur-sm">
      <div className="container mx-auto flex items-center justify-between px-4 py-4">
        <Link href="/compare" className="flex items-center gap-2" prefetch={true}>
          <Image
            src="/icon.svg"
            alt="WhichGLP Logo"
            width={40}
            height={40}
            className="h-10 w-10"
            priority
            loading="eager"
          />
          <div className="text-2xl font-bold text-foreground">
            Which<span className="text-primary">GLP</span>
          </div>
        </Link>

        {/* Desktop Navigation */}
        <div className="hidden items-center gap-8 md:flex">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              prefetch={true}
              className="text-sm text-muted-foreground transition-colors hover:text-foreground"
            >
              {link.label}
            </Link>
          ))}
        </div>

        {/* Mobile Hamburger Menu */}
        <Sheet open={open} onOpenChange={setOpen}>
          <SheetTrigger asChild className="md:hidden">
            <Button variant="ghost" size="icon">
              <Menu className="h-6 w-6" />
              <span className="sr-only">Toggle menu</span>
            </Button>
          </SheetTrigger>
          <SheetContent side="right" className="p-6">
            <nav className="flex flex-col gap-2 mt-12">
              {navLinks.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  prefetch={true}
                  onClick={() => setOpen(false)}
                  className="text-xl font-medium text-foreground transition-colors hover:text-primary py-4 px-2 rounded-lg hover:bg-muted/50 active:bg-muted"
                >
                  {link.label}
                </Link>
              ))}
            </nav>
          </SheetContent>
        </Sheet>
      </div>
    </nav>
  );
};

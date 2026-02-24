"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

const ComparePage = () => {
  const router = useRouter();

  useEffect(() => {
    router.replace("/");
  }, [router]);

  return null;
};

export default ComparePage;

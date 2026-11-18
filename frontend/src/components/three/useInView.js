import { useEffect, useState } from "react";

// Canvas nằm ngoài màn hình thì dừng vẽ (trang dài có nhiều cảnh 3D)
export function useInView(ref, margin = "200px") {
  const [inView, setInView] = useState(true);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const io = new IntersectionObserver(([e]) => setInView(e.isIntersecting), { rootMargin: margin });
    io.observe(el);
    return () => io.disconnect();
  }, [ref, margin]);
  return inView;
}

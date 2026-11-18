import { useEffect, useRef } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import * as THREE from "three";
import { BACK_URL, CardBody, CardLights, useLazyTexture } from "./three/cardShared.jsx";
import { useInView } from "./three/useInView.js";

// Một lá 3D lớn ở trang chi tiết. Kéo ngang để xoay (thả tay thì xoay tiếp theo quán tính), kéo dọc để nghiêng nhẹ.
const IDLE_SPEED = 0.35; // rad/s, tự xoay chậm khi không ai chạm

function SpinningCard({ frontUrl, reversed, controls, onReady, reduceMotion }) {
  const group = useRef();
  const state = useRef({ vel: reduceMotion ? 0 : 9, tilt: 0, dragging: false, lastX: 0, lastY: 0, lastT: 0 });
  const { gl } = useThree();
  const front = useLazyTexture(frontUrl);
  const back = useLazyTexture(BACK_URL);

  useEffect(() => {
    if (front && back) onReady?.();
  }, [front, back, onReady]);

  // Nút bấm ngoài canvas (bàn phím / người không kéo được) điều khiển qua ref này
  useEffect(() => {
    if (controls) controls.current = { spin: (v) => (state.current.vel = v) };
  }, [controls]);

  useEffect(() => {
    const el = gl.domElement;
    const s = state.current;
    const down = (e) => {
      Object.assign(s, { dragging: true, lastX: e.clientX, lastY: e.clientY, lastT: performance.now() });
      el.setPointerCapture(e.pointerId);
    };
    const move = (e) => {
      if (!s.dragging) return;
      const now = performance.now();
      const dx = e.clientX - s.lastX;
      group.current.rotation.y += dx * 0.012;
      s.vel = (dx * 0.012) / (Math.max(now - s.lastT, 1) / 1000);
      s.tilt = THREE.MathUtils.clamp(s.tilt + (e.clientY - s.lastY) * 0.004, -0.45, 0.45);
      Object.assign(s, { lastX: e.clientX, lastY: e.clientY, lastT: now });
    };
    const up = () => {
      s.dragging = false;
      s.tilt = 0;
    };
    el.addEventListener("pointerdown", down);
    el.addEventListener("pointermove", move);
    el.addEventListener("pointerup", up);
    el.addEventListener("pointercancel", up);
    return () => {
      el.removeEventListener("pointerdown", down);
      el.removeEventListener("pointermove", move);
      el.removeEventListener("pointerup", up);
      el.removeEventListener("pointercancel", up);
    };
  }, [gl]);

  useFrame(({ clock }, delta) => {
    const s = state.current;
    const g = group.current;
    if (!s.dragging) {
      g.rotation.y += s.vel * delta;
      const idle = reduceMotion ? 0 : IDLE_SPEED;
      s.vel += (idle - s.vel) * Math.min(1, delta * 1.6); // quán tính giảm dần về tốc độ tự xoay
    }
    g.rotation.x += (s.tilt - g.rotation.x) * Math.min(1, delta * 8);
    if (!reduceMotion) g.position.y = Math.sin(clock.elapsedTime * 1.2) * 0.04;
  });

  return (
    <group ref={group}>
      <CardBody front={front} back={back} reversed={reversed} />
    </group>
  );
}

export default function CardModel3D({ card, reversed = false, controls, onReady, className = "card-canvas" }) {
  const reduceMotion = typeof matchMedia !== "undefined" && matchMedia("(prefers-reduced-motion: reduce)").matches;
  const ref = useRef(null);
  const inView = useInView(ref);
  return (
    <Canvas ref={ref} frameloop={inView ? "always" : "never"} className={className} camera={{ position: [0, 0, 4.2], fov: 40 }} dpr={[1, 2]} gl={{ alpha: true, antialias: true }}>
      <CardLights />
      <SpinningCard frontUrl={card.image_url} reversed={reversed} controls={controls} onReady={onReady} reduceMotion={reduceMotion} />
    </Canvas>
  );
}

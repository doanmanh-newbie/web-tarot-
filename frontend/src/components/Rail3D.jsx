import { useEffect, useRef, useState } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import * as THREE from "three";
import { BACK_URL, CardBody, CardLights, useLazyTexture, W } from "./three/cardShared.jsx";
import { RING } from "./three/constants.js";
import { useInView } from "./three/useInView.js";

// Hàng lá bài 3D trong một canvas duy nhất (78 canvas riêng sẽ quá nặng cho trình duyệt).
// Dùng chung cho: lướt bộ bài, mục đã thích, bốc bài, xem lá đã bốc.
//   mode="pick"   như rail nhưng chạm lá nào là chọn lá đó (onPick); lá đã chọn nhô lên
//   mode="rail"   hàng ngang: kéo/vuốt/lăn chuột để lướt, thả tay thì trôi rồi hít vào lá gần nhất
//   mode="ring"   RING lá đầu xếp thành vòng tròn và xoay nhanh dần (xào bài)
//   mode="reveal" vòng chậm lại, lùi ra sau; các lá trong `chosen` bay ra hàng phía trước
// items: [{ key, image_url, reversed?, faceDown?, gone?, lift? }] — lift: lá vừa chạm nhô ra giữa khung và to dần — faceDown đổi thì lá lật 3D tại chỗ.
// loop: hàng ngang nối đầu với cuối thành vòng lướt mãi không hết.
// Lá luôn trượt mượt tới vị trí mới, nên đổi mode là cả bộ bài tự biến hình.
const SPACING = W + 0.5; // khoảng cách lá ở hàng phía trước (mode reveal)
const CAM_Z = 5.3;
const DEPTH = 0.9; // hàng ngang: mỗi vị trí lệch giữa lùi ra sau chừng này
// Hệ số phối cảnh của lá ngoài cùng (lệch 3 vị trí) — dùng để trải 7 lá vừa kín bề ngang khung
const F3 = CAM_Z / (CAM_Z + 3 * DEPTH);
const PAD = 0.045; // đệm mỗi bên, theo tỉ lệ bề ngang khung
const VISIBLE = 3.6; // hàng ngang: lá giữa + 3 lá mỗi bên = 7 lá; lá ra tới mép thì thu nhỏ dần rồi ẩn
const EDGE = 0.6; // quãng (tính theo lá) thu nhỏ ở mép: lá thứ 3 mỗi bên vẫn đủ cỡ
const PRELOAD = 5; // hàng ngang: tải ảnh trước cho các lá cách giữa không quá 5 vị trí
const RING_R = 2.7; // bán kính vòng tròn
const SPIN = { rail: 0, pick: 0, ring: 4.5, reveal: 0.15 }; // tốc độ xoay vòng (rad/s) theo mode
const SLIDE = 3; // tốc độ hàng trượt tới lá đích (càng nhỏ càng chậm)
const sliding = (m) => m === "rail" || m === "pick"; // các mode kéo/lướt được
// Khoảng cách có dấu từ a tới b trên vòng n lá, trong [-n/2, n/2)
const wrap = (d, n) => (((d % n) + n * 1.5) % n) - n / 2;

const target = new THREE.Vector3();

function RailCard({ item, index, st, back, onTap, reduceMotion, mode, slot, slots }) {
  const ref = useRef();
  const frontMat = useRef();
  const [near, setNear] = useState(false);
  const front = useLazyTexture(item.image_url, near && !!item.image_url);
  const flip = useRef(item.faceDown ? Math.PI : 0);
  const placed = useRef(false);

  useFrame(({ clock }, delta) => {
    const g = ref.current;
    const s = st.current;
    const t = clock.elapsedTime;
    flip.current += ((item.faceDown ? Math.PI : 0) - flip.current) * Math.min(1, delta * (reduceMotion ? 30 : 4));

    let x, y, z, ry, scale, light, visible;
    if (sliding(mode)) {
      const d = s.loop ? wrap(index - s.offset, s.n) : index - s.offset;
      const a = Math.abs(d);
      const center = Math.max(0, 1 - a * 2); // 1 khi đúng giữa, 0 khi lệch nửa lá
      visible = a < VISIBLE && !item.gone; // gone: lá đã được rút khỏi bộ
      if (visible && a < PRELOAD && !near) setNear(true);
      x = d * s.spacing;
      y = reduceMotion ? 0 : Math.sin(t * 1.2 + index) * 0.04 * center;
      z = -Math.min(a, 4) * DEPTH;
      // Lá hai bên xoay mặt vào giữa; lá giữa đung đưa nhẹ để thấy rõ là vật thể 3D
      ry = -THREE.MathUtils.clamp(d, -1, 1) * 0.55 + (reduceMotion ? 0 : Math.sin(t * 0.8) * 0.22 * center);
      scale = (1.12 - Math.min(a, 3) * 0.08) * Math.min(1, (VISIBLE - a) / EDGE);
      light = 1 - Math.min(a, 3) * 0.2;
      if (item.lift) {
        // Lá vừa chạm: ra giữa khung, tiến về phía trước và to dần (trước khi bay xuống khay)
        visible = true;
        x = 0;
        y = 0.05;
        z = 0.6;
        ry = 0;
        scale = 1.05;
      }
    } else if (mode === "reveal" && slot >= 0) {
      // Lá được rút: bay ra hàng phía trước, đung đưa nhẹ
      if (!near) setNear(true);
      x = (slot - (slots - 1) / 2) * Math.min(SPACING, 7 / Math.max(slots, 1));
      y = 0.1 + (reduceMotion ? 0 : Math.sin(t * 1.3 + slot) * 0.05);
      z = 1.1;
      ry = reduceMotion ? 0 : Math.sin(t * 0.7 + slot) * 0.12;
      scale = slots > 3 ? 0.78 : 0.92;
      light = 1;
      visible = true;
    } else {
      // Vòng tròn quay quanh trục dọc; lá phía trước sáng, phía sau tối
      visible = index < RING;
      const ang = (index / RING) * Math.PI * 2 + s.spin;
      const behind = mode === "reveal";
      x = Math.sin(ang) * RING_R;
      z = Math.cos(ang) * RING_R - RING_R - (behind ? 2.6 : 0.6);
      y = behind ? -0.35 : 0;
      ry = ang;
      scale = behind ? 0.62 : 0.78;
      light = (0.45 + 0.55 * (Math.cos(ang) + 1) / 2) * (behind ? 0.55 : 1);
    }

    // Lá vừa hiện lại (vd. vòng lặp đưa từ mép này sang mép kia) thì đặt thẳng, không bay ngang màn hình
    const k = placed.current && g.visible ? Math.min(1, delta * (item.lift ? 3.2 : sliding(mode) ? 9 : 4.5)) : 1;
    g.visible = visible;
    if (!visible) return;
    placed.current = true;
    g.position.lerp(target.set(x, y, z), k);
    g.rotation.y += (ry + flip.current - g.rotation.y) * k;
    g.scale.setScalar(g.scale.x + (scale - g.scale.x) * k);
    if (frontMat.current?.map) frontMat.current.color.setScalar(light);
  });

  return (
    <group
      ref={ref}
      onClick={(e) => {
        e.stopPropagation();
        onTap(index);
      }}
      onPointerOver={() => (document.body.style.cursor = "pointer")}
      onPointerOut={() => (document.body.style.cursor = "")}
    >
      <CardBody front={front} back={back} frontRef={frontMat} reversed={item.reversed} />
    </group>
  );
}

function RailScene({ items, api, mode = "rail", loop = false, chosen = [], onActive, onOpen, onPick, onNeedMore, reduceMotion }) {
  const st = useRef({ offset: 0, target: 0, vel: 0, drag: false, moved: false, lastX: 0, lastT: 0, active: -1, spin: 0, spinVel: 0 });
  const { gl, size, viewport } = useThree();
  const back = useLazyTexture(BACK_URL);
  const nRef = useRef(items.length);
  nRef.current = items.length;
  // Vòng lặp chỉ khi đủ lá để không thấy cùng một lá ở hai mép
  st.current.n = items.length;
  st.current.loop = loop && items.length > VISIBLE * 2;
  const modeRef = useRef(mode);
  modeRef.current = mode;
  // Khoảng cách lá trên hàng ngang: 7 lá trải kín bề ngang khung (chừa đệm PAD), tối thiểu không chồng lá
  const halfOuter = (W / 2) * (1.12 - 3 * 0.08); // nửa bề rộng lá ngoài cùng
  st.current.spacing = Math.max(W + 0.25, (viewport.width * (0.5 - PAD) - halfOuter * F3) / (3 * F3));
  const pxPerSlot = (size.width / viewport.width) * st.current.spacing; // số pixel tương ứng một lá

  useEffect(() => {
    api.current = {
      goTo: (i) => {
        const s = st.current;
        s.target = s.loop ? Math.round(s.target) + wrap(i - Math.round(s.target), s.n) : THREE.MathUtils.clamp(i, 0, nRef.current - 1);
      },
    };
  }, [api]);

  useEffect(() => {
    const el = gl.domElement;
    const s = st.current;
    const down = (e) => {
      s.moved = false;
      if (!sliding(modeRef.current)) return; // đang xoay/rút bài thì không cho kéo hàng
      Object.assign(s, { drag: true, lastX: e.clientX, lastT: performance.now(), vel: 0, startX: e.clientX });
    };
    const move = (e) => {
      if (!s.drag) return;
      if (!s.moved && Math.abs(e.clientX - s.startX) > 5) {
        s.moved = true;
        el.setPointerCapture(e.pointerId);
      }
      if (!s.moved) return;
      const now = performance.now();
      const dSlots = (e.clientX - s.lastX) / pxPerSlot;
      s.offset -= dSlots;
      s.vel = s.vel * 0.5 + (-dSlots / (Math.max(now - s.lastT, 1) / 1000)) * 0.5; // lá/giây
      s.lastX = e.clientX;
      s.lastT = now;
    };
    const up = () => {
      if (!s.drag) return;
      s.drag = false;
      if (performance.now() - s.lastT > 80) s.vel = 0; // dừng tay rồi mới thả thì không trôi
      // Điểm dừng = vị trí hiện tại + quãng trôi theo đà, làm tròn về một lá
      s.target = Math.round(s.offset + s.vel * 0.35);
    };
    // Chỉ lăn ngang (touchpad, Shift + lăn) mới lướt hàng; lăn dọc vẫn cuộn trang dài như bình thường
    const wheel = (e) => {
      if (!sliding(modeRef.current)) return;
      const delta = e.shiftKey ? e.deltaY : Math.abs(e.deltaX) > Math.abs(e.deltaY) ? e.deltaX : 0;
      if (Math.abs(delta) < 2) return;
      e.preventDefault();
      clearTimeout(s.wheelT);
      s.wheelAcc = (s.wheelAcc ?? 0) + delta;
      // Gom các sự kiện lăn liên tiếp của touchpad thành từng bước một lá
      if (Math.abs(s.wheelAcc) > 60) {
        s.target = Math.round(s.target + Math.sign(s.wheelAcc));
        s.wheelAcc = 0;
      }
      s.wheelT = setTimeout(() => (s.wheelAcc = 0), 200);
    };
    el.addEventListener("pointerdown", down);
    el.addEventListener("pointermove", move);
    el.addEventListener("pointerup", up);
    el.addEventListener("pointercancel", up);
    el.addEventListener("wheel", wheel, { passive: false });
    return () => {
      el.removeEventListener("pointerdown", down);
      el.removeEventListener("pointermove", move);
      el.removeEventListener("pointerup", up);
      el.removeEventListener("pointercancel", up);
      el.removeEventListener("wheel", wheel);
    };
  }, [gl, pxPerSlot]);

  useFrame((_, delta) => {
    const s = st.current;
    // Vòng tròn tăng/giảm tốc từ từ: cảm giác bộ bài được quay rồi hãm lại
    const spinTarget = reduceMotion ? Math.min(SPIN[mode], 1) : SPIN[mode];
    s.spinVel += (spinTarget - s.spinVel) * Math.min(1, delta * (mode === "ring" ? 1.4 : 0.9));
    s.spin += s.spinVel * delta;
    if (!sliding(mode)) return;

    const max = Math.max(0, nRef.current - 1);
    if (!s.drag) {
      if (!s.loop) s.target = THREE.MathUtils.clamp(s.target, 0, max);
      s.offset += (s.target - s.offset) * Math.min(1, delta * (reduceMotion ? 20 : SLIDE));
    } else if (!s.loop) {
      s.offset = THREE.MathUtils.clamp(s.offset, -0.4, max + 0.4); // kéo quá đầu/cuối thì chỉ nhích nhẹ
    }
    const r = Math.round(s.offset);
    const active = s.loop ? ((r % s.n) + s.n) % s.n : THREE.MathUtils.clamp(r, 0, max);
    if (active !== s.active) {
      s.active = active;
      onActive?.(active);
    }
    if (onNeedMore && !s.loop && s.offset > nRef.current - 8) onNeedMore();
  });

  const tap = (i) => {
    const s = st.current;
    if (s.moved) return; // vừa kéo xong thì không coi là bấm
    if (mode === "reveal") {
      const slot = chosen.indexOf(i);
      if (slot >= 0) onOpen?.(slot);
    } else if (mode === "pick") {
      if (!chosen.includes(i)) onPick?.(i);
    } else if (mode === "rail") {
      // Chạm lá nào cũng mở luôn (và đưa lá đó vào giữa), không bắt chạm hai lần
      api.current.goTo(i);
      onOpen?.(i);
    }
  };

  return items.map((it, i) => (
    <RailCard
      key={it.key}
      item={it}
      index={i}
      st={st}
      back={back}
      onTap={tap}
      reduceMotion={reduceMotion}
      mode={mode}
      slot={chosen.indexOf(i)}
      slots={chosen.length}
    />
  ));
}

export default function Rail3D(props) {
  const reduceMotion = typeof matchMedia !== "undefined" && matchMedia("(prefers-reduced-motion: reduce)").matches;
  const ref = useRef(null);
  const inView = useInView(ref);
  return (
    <Canvas ref={ref} frameloop={inView ? "always" : "never"} className="rail-canvas" camera={{ position: [0, 0.1, CAM_Z], fov: 34 }} dpr={[1, 1.5]} gl={{ alpha: true, antialias: true }}>
      <CardLights />
      <RailScene {...props} reduceMotion={reduceMotion} />
    </Canvas>
  );
}

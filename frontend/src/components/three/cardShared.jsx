import { useEffect, useState } from "react";
import * as THREE from "three";

// Kích thước lá bài trong không gian 3D (tỉ lệ 7:12 như ảnh)
export const W = 1.4;
export const H = 2.4;
export const R = 0.08;
export const DEPTH = 0.035;
export const BACK_URL = "/card-back.webp";

function roundedRect() {
  const s = new THREE.Shape();
  const x = -W / 2;
  const y = -H / 2;
  s.moveTo(x + R, y);
  s.lineTo(x + W - R, y);
  s.quadraticCurveTo(x + W, y, x + W, y + R);
  s.lineTo(x + W, y + H - R);
  s.quadraticCurveTo(x + W, y + H, x + W - R, y + H);
  s.lineTo(x + R, y + H);
  s.quadraticCurveTo(x, y + H, x, y + H - R);
  s.lineTo(x, y + R);
  s.quadraticCurveTo(x, y, x + R, y);
  return s;
}

let shared = null;
// Một bộ hình khối dùng chung cho mọi lá (78 lá không tạo 78 bản sao)
export function getCardGeometry() {
  if (shared) return shared;
  const shape = roundedRect();
  const body = new THREE.ExtrudeGeometry(shape, { depth: DEPTH, bevelEnabled: false, curveSegments: 8 });
  body.translate(0, 0, -DEPTH / 2);
  // ShapeGeometry không có UV 0..1 sẵn: tự trải ảnh khớp khung chữ nhật
  const face = new THREE.ShapeGeometry(shape, 8);
  const p = face.attributes.position;
  const uv = face.attributes.uv;
  for (let i = 0; i < p.count; i++) uv.setXY(i, (p.getX(i) + W / 2) / W, (p.getY(i) + H / 2) / H);
  shared = { body, face };
  return shared;
}

const loader = new THREE.TextureLoader();
const cache = new Map();

// Tải ảnh làm texture khi `enabled` (lá sắp vào khung nhìn); ảnh đã tải được dùng lại.
// shortcut: không giải phóng texture của lá đã lướt qua; 78 lá × ~3 MB GPU vẫn ổn trên máy thường.
export function useLazyTexture(url, enabled = true) {
  const [tex, setTex] = useState(() => cache.get(url)?.tex ?? null);
  useEffect(() => {
    if (!enabled || tex) return;
    let entry = cache.get(url);
    if (!entry) {
      entry = {
        promise: new Promise((resolve, reject) =>
          loader.load(
            url,
            (t) => {
              t.colorSpace = THREE.SRGBColorSpace;
              t.anisotropy = 8;
              entry.tex = t;
              resolve(t);
            },
            undefined,
            reject,
          ),
        ),
      };
      cache.set(url, entry);
    }
    let alive = true;
    entry.promise.then((t) => alive && setTex(t)).catch(() => cache.delete(url));
    return () => {
      alive = false;
    };
  }, [url, enabled, tex]);
  return tex;
}

// Thân lá (cạnh vàng) + mặt trước + mặt sau. Chưa có ảnh thì hiện màu nâu tạm.
export function CardBody({ front, back, reversed = false, frontRef }) {
  const { body, face } = getCardGeometry();
  return (
    <group rotation-z={reversed ? Math.PI : 0}>
      <mesh geometry={body}>
        <meshStandardMaterial color="#b08a3e" metalness={0.75} roughness={0.32} />
      </mesh>
      <mesh geometry={face} position-z={DEPTH / 2 + 0.001}>
        <meshStandardMaterial ref={frontRef} map={front} color={front ? "#ffffff" : "#3a2516"} transparent alphaTest={0.5} roughness={0.6} key={front ? "f" : "p"} />
      </mesh>
      <mesh geometry={face} position-z={-DEPTH / 2 - 0.001} rotation-y={Math.PI}>
        <meshStandardMaterial map={back} color={back ? "#ffffff" : "#3a2516"} transparent alphaTest={0.5} roughness={0.6} key={back ? "b" : "p"} />
      </mesh>
    </group>
  );
}

export function CardLights() {
  return (
    <>
      <ambientLight intensity={0.9} />
      <directionalLight position={[3, 4, 5]} intensity={2.2} />
      <pointLight position={[-3, -2, 3]} intensity={18} color="#ffcf7a" />
      <pointLight position={[0, 2, -4]} intensity={14} color="#ffe2a8" />
    </>
  );
}

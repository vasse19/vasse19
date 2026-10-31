import React, { useLayoutEffect, useMemo } from "react";
import {
  AbsoluteFill,
  Audio,
  Easing,
  interpolate,
  Sequence,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { ThreeCanvas } from "@remotion/three";
import { useThree } from "@react-three/fiber";
import * as THREE from "three";
import { FontLoader } from "three/examples/jsm/loaders/FontLoader.js";
import { TextGeometry } from "three/examples/jsm/geometries/TextGeometry.js";
import { RoomEnvironment } from "three/examples/jsm/environments/RoomEnvironment.js";
import fontJson from "./inter-display-black.typeface.json";

// Timeline (30 fps, 150 frames): VASS letters fly in 8-40, slam at 44, vinyl rises,
// light sweep 70-100, tagline at 96, slow orbit throughout.
const LAND = 44;

const font = new FontLoader().parse(fontJson as never);

const seeded = (seed: number) => {
  let s = seed;
  return () => (s = (s * 16807) % 2147483647) / 2147483647;
};

// Reflections without network: three's built-in studio room as the environment map.
const Environment: React.FC = () => {
  const { gl, scene } = useThree();
  useLayoutEffect(() => {
    const pmrem = new THREE.PMREMGenerator(gl);
    const env = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
    scene.environment = env;
    return () => {
      env.dispose();
      pmrem.dispose();
    };
  }, [gl, scene]);
  return null;
};

const useGold = () =>
  useMemo(
    () =>
      new THREE.MeshPhysicalMaterial({
        color: new THREE.Color("#ffc23d"),
        metalness: 1,
        roughness: 0.2,
        clearcoat: 0.6,
        clearcoatRoughness: 0.15,
        envMapIntensity: 1.35,
      }),
    [],
  );

// One geometry per letter so each can fly in on its own; x offsets come from the glyph advances.
const useLetters = (text: string, size: number, depth: number) =>
  useMemo(() => {
    const res = (fontJson as { resolution: number }).resolution;
    const glyphs = (fontJson as { glyphs: Record<string, { ha: number }> }).glyphs;
    let x = 0;
    const letters = [...text].map((ch) => {
      const geo = new TextGeometry(ch, {
        font,
        size,
        depth,
        curveSegments: 10,
        bevelEnabled: true,
        bevelThickness: depth * 0.18,
        bevelSize: size * 0.035,
        bevelSegments: 5,
      });
      geo.computeBoundingBox();
      const bb = geo.boundingBox!;
      const cx = (bb.max.x + bb.min.x) / 2;
      geo.translate(-cx, -(bb.max.y + bb.min.y) / 2, -depth / 2);
      const out = { ch, geo, x: x + cx };
      x += (glyphs[ch].ha / res) * size + size * 0.02;
      return out;
    });
    const width = x - size * 0.02;
    return letters.map((l) => ({ ...l, x: l.x - width / 2 }));
  }, [text, size, depth]);

const Word: React.FC<{
  text: string;
  size: number;
  depth: number;
  y: number;
  start: number;
  stagger: number;
  from: "depth" | "above";
}> = ({ text, size, depth, y, start, stagger, from }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const gold = useGold();
  const letters = useLetters(text, size, depth);
  return (
    <group position={[0, y, 0]}>
      {letters.map((l, i) => {
        const t0 = start + i * stagger;
        const p = spring({ frame: frame - t0, fps, config: { damping: 15, stiffness: 120, mass: 0.9 } });
        const z = from === "depth" ? interpolate(p, [0, 1], [-38, 0]) : 0;
        const dy = from === "above" ? interpolate(p, [0, 1], [4.5, 0]) : 0;
        const spin = interpolate(p, [0, 1], [from === "depth" ? Math.PI * 1.6 : -Math.PI * 0.6, 0]);
        const s = interpolate(p, [0, 1], [0.25, 1]);
        return (
          <mesh
            key={i}
            geometry={l.geo}
            material={gold}
            position={[l.x, dy, z]}
            rotation={[from === "above" ? spin : 0, from === "depth" ? spin : 0, 0]}
            scale={frame < t0 ? 0.0001 : s}
          />
        );
      })}
    </group>
  );
};

// Vinyl record: grooves drawn once on a canvas (deterministic), gold label in the centre.
const Vinyl: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const grooves = useMemo(() => {
    const c = document.createElement("canvas");
    c.width = c.height = 1024;
    const g = c.getContext("2d")!;
    g.fillStyle = "#0b0b0d";
    g.fillRect(0, 0, 1024, 1024);
    for (let r = 150; r < 510; r += 3) {
      g.strokeStyle = r % 9 === 0 ? "#26262b" : "#141417";
      g.lineWidth = 1.4;
      g.beginPath();
      g.arc(512, 512, r, 0, Math.PI * 2);
      g.stroke();
    }
    // painted sheen: two soft light wedges across the grooves, as on a lit record
    for (const [from, to] of [[-0.5, -0.1], [Math.PI - 0.5, Math.PI - 0.1]]) {
      const grad = g.createRadialGradient(512, 512, 150, 512, 512, 510);
      grad.addColorStop(0, "rgba(255,255,255,0.05)");
      grad.addColorStop(1, "rgba(255,255,255,0.16)");
      g.fillStyle = grad;
      g.beginPath();
      g.moveTo(512, 512);
      g.arc(512, 512, 510, from, to);
      g.closePath();
      g.fill();
    }
    const tex = new THREE.CanvasTexture(c);
    tex.colorSpace = THREE.SRGBColorSpace;
    return tex;
  }, []);
  const vinyl = useMemo(
    () => new THREE.MeshBasicMaterial({ map: grooves }),
    [grooves],
  );
  const label = useMemo(
    () => new THREE.MeshStandardMaterial({ color: "#d9971c", metalness: 0.85, roughness: 0.42, envMapIntensity: 0.55 }),
    [],
  );
  const p = spring({ frame: frame - (LAND - 6), fps, config: { damping: 18, stiffness: 90 } });
  return (
    <group position={[0, interpolate(p, [0, 1], [-7, 0.15]), -2.4]} rotation={[Math.PI / 2 - 0.12, 0, 0]} scale={interpolate(p, [0, 1], [0.6, 1])}>
      <group rotation={[0, -frame * 0.045, 0]}>
        <mesh material={vinyl}>
          <cylinderGeometry args={[4.4, 4.4, 0.08, 128]} />
        </mesh>
        <mesh material={label} position={[0, 0.05, 0]}>
          <cylinderGeometry args={[1.35, 1.35, 0.04, 96]} />
        </mesh>
        <mesh position={[0, 0.08, 0]}>
          <cylinderGeometry args={[0.12, 0.12, 0.06, 32]} />
          <meshStandardMaterial color="#050505" />
        </mesh>
      </group>
    </group>
  );
};

const Sparks: React.FC = () => {
  const frame = useCurrentFrame();
  const { positions, base } = useMemo(() => {
    const rnd = seeded(7);
    const n = 260;
    const b = new Float32Array(n * 3);
    for (let i = 0; i < n; i++) {
      b[i * 3] = (rnd() - 0.5) * 22;
      b[i * 3 + 1] = (rnd() - 0.5) * 13;
      b[i * 3 + 2] = (rnd() - 0.5) * 10 - 1;
    }
    return { positions: new Float32Array(b), base: b };
  }, []);
  for (let i = 0; i < positions.length; i += 3) {
    const rise = ((base[i + 1] + 6.5 + frame * 0.025 * (1 + (i % 7) * 0.12)) % 13) - 6.5;
    positions[i] = base[i] + Math.sin(frame * 0.03 + i) * 0.15;
    positions[i + 1] = rise;
    positions[i + 2] = base[i + 2];
  }
  const geo = useMemo(() => new THREE.BufferGeometry(), []);
  geo.setAttribute("position", new THREE.BufferAttribute(positions, 3));
  const opacity = interpolate(frame, [LAND - 4, LAND + 10], [0.15, 0.85], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <points geometry={geo}>
      <pointsMaterial color="#ffd36b" size={0.07} transparent opacity={opacity} depthWrite={false} blending={THREE.AdditiveBlending} />
    </points>
  );
};

const Shockwave: React.FC = () => {
  const frame = useCurrentFrame();
  const k = interpolate(frame, [LAND, LAND + 22], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  if (frame < LAND || k >= 1) return null;
  return (
    <mesh position={[0, -0.2, 0.5]} scale={0.5 + k * 9}>
      <torusGeometry args={[1, 0.035, 12, 128]} />
      <meshBasicMaterial color="#ffe08a" transparent opacity={1 - k} blending={THREE.AdditiveBlending} depthWrite={false} />
    </mesh>
  );
};

const Scene: React.FC = () => {
  const frame = useCurrentFrame();
  // camera stays put; the whole world turns slowly (orbit), with a small kick on the slam
  const orbit = interpolate(frame, [0, 150], [-0.42, 0.14], { easing: Easing.inOut(Easing.sin) });
  const kick = frame >= LAND ? Math.exp(-(frame - LAND) / 5) * Math.sin((frame - LAND) * 1.9) * 0.12 : 0;
  const sweepX = interpolate(frame, [68, 104], [-10, 10], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.cubic) });
  return (
    <>
      <Environment />
      <ambientLight intensity={0.15} />
      <directionalLight position={[6, 8, 10]} intensity={2.2} color="#fff1d6" />
      <directionalLight position={[-8, -2, 4]} intensity={0.8} color="#ff9a3c" />
      <pointLight position={[sweepX, 1.5, 4]} intensity={frame > 66 && frame < 108 ? 90 : 0} distance={14} color="#fffbe8" />
      <group rotation={[0.06 + kick * 0.3, orbit, 0]} position={[0, kick, 0]}>
        <Vinyl />
        <Word text="VASS" size={2.5} depth={0.8} y={-0.85} start={8} stagger={6} from="depth" />
        <Word text="MONSIEUR" size={0.92} depth={0.35} y={1.55} start={LAND - 4} stagger={2} from="above" />
        <Shockwave />
      </group>
      <Sparks />
    </>
  );
};

export const GoldIntro: React.FC = () => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const flash = interpolate(frame, [LAND - 1, LAND, LAND + 5], [0, 0.6, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const tagline = interpolate(frame, [96, 106], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const glow = interpolate(frame, [LAND - 6, LAND + 20], [0.25, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ background: "#050403" }}>
      <AbsoluteFill
        style={{
          background: `radial-gradient(ellipse 55% 60% at 50% 48%, rgba(255,170,40,${0.32 * glow}) 0%, rgba(90,45,5,${0.35 * glow}) 40%, rgba(5,4,3,1) 78%)`,
        }}
      />
      <ThreeCanvas width={width} height={height} camera={{ fov: 32, position: [0, 0, 15] }} gl={{ antialias: true, toneMapping: THREE.ACESFilmicToneMapping }}>
        <Scene />
      </ThreeCanvas>
      <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 120 }}>
        <div
          style={{
            opacity: tagline,
            filter: `blur(${(1 - tagline) * 8}px)`,
            fontFamily: "Inter, sans-serif",
            fontWeight: 700,
            fontSize: 38,
            letterSpacing: "0.32em",
            color: "#f3c860",
          }}
        >
          MONTAGE · MOTION DESIGN · MINIATURES
        </div>
      </AbsoluteFill>
      <AbsoluteFill style={{ background: "#fff6dc", opacity: flash }} />
      <Sequence from={4}>
        <Audio src={staticFile("sfx/whoosh.mp3")} volume={0.55} />
      </Sequence>
      <Sequence from={LAND - 2}>
        <Audio src={staticFile("sfx/impact-bass-1.mp3")} volume={0.42} />
      </Sequence>
      <Sequence from={76}>
        <Audio src={staticFile("sfx/sparkle.mp3")} volume={0.38} />
      </Sequence>
    </AbsoluteFill>
  );
};

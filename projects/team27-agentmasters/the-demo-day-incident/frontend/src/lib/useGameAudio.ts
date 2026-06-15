"use client";

import { useEffect, useRef, useState } from "react";
import {
  AudioDirector,
  type AudioScene,
  type SoundEffect,
} from "@/lib/audioDirector";

export function useGameAudio(scene: AudioScene) {
  const directorRef = useRef<AudioDirector | null>(null);
  const [muted, setMutedState] = useState(false);

  useEffect(() => {
    const director = new AudioDirector();

    directorRef.current = director;
    const mutedStateTimer = window.setTimeout(() => {
      setMutedState(director.getMuted());
    }, 0);

    const activate = () => {
      void director.activate();
    };

    window.addEventListener("pointerdown", activate, { once: true });
    window.addEventListener("keydown", activate, { once: true });

    return () => {
      window.clearTimeout(mutedStateTimer);
      window.removeEventListener("pointerdown", activate);
      window.removeEventListener("keydown", activate);
      director.dispose();

      if (directorRef.current === director) {
        directorRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    directorRef.current?.setScene(scene);
  }, [scene]);

  function setMuted(nextMuted: boolean) {
    directorRef.current?.setMuted(nextMuted);
    setMutedState(nextMuted);
  }

  function play(effect: SoundEffect) {
    directorRef.current?.play(effect);
  }

  return {
    muted,
    setMuted,
    play,
  };
}

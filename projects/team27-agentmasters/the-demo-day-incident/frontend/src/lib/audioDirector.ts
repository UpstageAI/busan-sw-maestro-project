export type AudioScene =
  | "idle"
  | "intro"
  | "investigation"
  | "interrogation"
  | "deduction"
  | "success"
  | "failure";

export type SoundEffect =
  | "cardOpen"
  | "messageSend"
  | "messageReceive"
  | "system"
  | "unlock"
  | "error"
  | "select";

type ActiveTrack = {
  bus: GainNode;
  timerId: number;
  stop: () => void;
};

type SceneConfig = {
  notes: number[];
  bassNotes: number[];
  waveform: OscillatorType;
  pulseWaveform: OscillatorType;
  phraseSeconds: number;
  volume: number;
  detune: number;
};

const MUTE_STORAGE_KEY = "demo-day-incident-audio-muted";
const MASTER_VOLUME = 0.72;
const MUSIC_FADE_SECONDS = 1.2;

const SCENE_CONFIGS: Record<Exclude<AudioScene, "idle">, SceneConfig> = {
  intro: {
    notes: [110, 130.81, 164.81, 146.83],
    bassNotes: [55, 65.41],
    waveform: "sine",
    pulseWaveform: "triangle",
    phraseSeconds: 8,
    volume: 0.13,
    detune: 7,
  },
  investigation: {
    notes: [110, 123.47, 146.83, 138.59],
    bassNotes: [55, 61.74, 73.42, 69.3],
    waveform: "triangle",
    pulseWaveform: "sine",
    phraseSeconds: 8,
    volume: 0.105,
    detune: 4,
  },
  interrogation: {
    notes: [98, 116.54, 130.81, 110],
    bassNotes: [49, 58.27, 55, 46.25],
    waveform: "triangle",
    pulseWaveform: "square",
    phraseSeconds: 6,
    volume: 0.095,
    detune: 3,
  },
  deduction: {
    notes: [82.41, 98, 110, 123.47],
    bassNotes: [41.2, 49, 55, 61.74],
    waveform: "sawtooth",
    pulseWaveform: "triangle",
    phraseSeconds: 6,
    volume: 0.085,
    detune: 2,
  },
  success: {
    notes: [130.81, 164.81, 196, 261.63],
    bassNotes: [65.41, 82.41, 98, 130.81],
    waveform: "sine",
    pulseWaveform: "triangle",
    phraseSeconds: 8,
    volume: 0.12,
    detune: 6,
  },
  failure: {
    notes: [73.42, 69.3, 58.27, 55],
    bassNotes: [36.71, 34.65, 29.14, 27.5],
    waveform: "sawtooth",
    pulseWaveform: "square",
    phraseSeconds: 7,
    volume: 0.075,
    detune: 1,
  },
};

export class AudioDirector {
  private context: AudioContext | null = null;
  private masterGain: GainNode | null = null;
  private musicGain: GainNode | null = null;
  private effectsGain: GainNode | null = null;
  private activeTrack: ActiveTrack | null = null;
  private desiredScene: AudioScene = "idle";
  private muted = false;

  constructor() {
    if (typeof window === "undefined") {
      return;
    }

    this.muted = localStorage.getItem(MUTE_STORAGE_KEY) === "true";
  }

  getMuted() {
    return this.muted;
  }

  async activate() {
    const context = this.ensureContext();

    if (!context) {
      return;
    }

    if (context.state === "suspended") {
      await context.resume();
    }

    if (!this.activeTrack && this.desiredScene !== "idle") {
      this.startScene(this.desiredScene);
    }
  }

  setScene(scene: AudioScene) {
    this.desiredScene = scene;

    if (!this.context || this.context.state !== "running") {
      return;
    }

    this.startScene(scene);
  }

  setMuted(muted: boolean) {
    this.muted = muted;
    localStorage.setItem(MUTE_STORAGE_KEY, String(muted));

    if (!this.context || !this.masterGain) {
      return;
    }

    const now = this.context.currentTime;
    this.masterGain.gain.cancelScheduledValues(now);
    this.masterGain.gain.setTargetAtTime(
      muted ? 0 : MASTER_VOLUME,
      now,
      0.035,
    );
  }

  play(effect: SoundEffect) {
    const context = this.context;
    const output = this.effectsGain;

    if (!context || !output || context.state !== "running" || this.muted) {
      return;
    }

    const now = context.currentTime;

    switch (effect) {
      case "cardOpen":
        this.playNoiseSweep(now, 0.13, 900, 260, 0.12);
        this.playTone(now, 220, 0.18, 0.07, "triangle", 330);
        break;
      case "messageSend":
        this.playTone(now, 440, 0.08, 0.08, "sine", 660);
        this.playTone(now + 0.055, 660, 0.1, 0.065, "sine", 880);
        break;
      case "messageReceive":
        this.playTone(now, 523.25, 0.12, 0.06, "sine", 493.88);
        this.playTone(now + 0.09, 659.25, 0.18, 0.055, "triangle", 587.33);
        break;
      case "system":
        this.playTone(now, 174.61, 0.25, 0.055, "sine", 130.81);
        this.playTone(now + 0.04, 349.23, 0.18, 0.035, "triangle", 261.63);
        break;
      case "unlock":
        [392, 523.25, 659.25, 783.99].forEach((frequency, index) => {
          this.playTone(
            now + index * 0.07,
            frequency,
            0.22,
            0.055,
            "sine",
            frequency * 1.02,
          );
        });
        break;
      case "error":
        this.playTone(now, 130.81, 0.18, 0.08, "square", 98);
        this.playTone(now + 0.12, 116.54, 0.26, 0.065, "sawtooth", 73.42);
        break;
      case "select":
        this.playTone(now, 330, 0.07, 0.045, "triangle", 370);
        break;
    }
  }

  dispose() {
    this.stopActiveTrack(0.08);

    if (this.context) {
      void this.context.close();
    }

    this.context = null;
    this.masterGain = null;
    this.musicGain = null;
    this.effectsGain = null;
  }

  private ensureContext() {
    if (this.context) {
      return this.context;
    }

    if (typeof window === "undefined") {
      return null;
    }

    const AudioContextConstructor =
      window.AudioContext ??
      (
        window as typeof window & {
          webkitAudioContext?: typeof AudioContext;
        }
      ).webkitAudioContext;

    if (!AudioContextConstructor) {
      return null;
    }

    const context = new AudioContextConstructor();
    const masterGain = context.createGain();
    const musicGain = context.createGain();
    const effectsGain = context.createGain();

    masterGain.gain.value = this.muted ? 0 : MASTER_VOLUME;
    musicGain.gain.value = 0.75;
    effectsGain.gain.value = 0.9;

    musicGain.connect(masterGain);
    effectsGain.connect(masterGain);
    masterGain.connect(context.destination);

    this.context = context;
    this.masterGain = masterGain;
    this.musicGain = musicGain;
    this.effectsGain = effectsGain;

    return context;
  }

  private startScene(scene: AudioScene) {
    if (!this.context || !this.musicGain) {
      return;
    }

    this.stopActiveTrack(MUSIC_FADE_SECONDS);

    if (scene === "idle") {
      return;
    }

    const context = this.context;
    const config = SCENE_CONFIGS[scene];
    const bus = context.createGain();
    const filter = context.createBiquadFilter();
    const activeNodes = new Set<AudioScheduledSourceNode>();
    let phraseIndex = 0;
    let stopped = false;

    bus.gain.setValueAtTime(0.0001, context.currentTime);
    bus.gain.exponentialRampToValueAtTime(
      config.volume,
      context.currentTime + MUSIC_FADE_SECONDS,
    );
    filter.type = "lowpass";
    filter.frequency.value = scene === "failure" ? 720 : 1250;
    filter.Q.value = 0.65;
    bus.connect(filter);
    filter.connect(this.musicGain);

    const schedulePhrase = () => {
      if (stopped || context.state !== "running") {
        return;
      }

      const startAt = context.currentTime + 0.08;
      const root = config.notes[phraseIndex % config.notes.length];
      const bass = config.bassNotes[phraseIndex % config.bassNotes.length];

      this.schedulePad(
        startAt,
        config.phraseSeconds + 0.4,
        [root, root * 1.5, root * 2],
        config,
        bus,
        activeNodes,
      );
      this.schedulePulsePattern(
        startAt,
        config.phraseSeconds,
        bass,
        config,
        bus,
        activeNodes,
      );
      phraseIndex += 1;
    };

    schedulePhrase();
    const timerId = window.setInterval(
      schedulePhrase,
      config.phraseSeconds * 1000,
    );

    this.activeTrack = {
      bus,
      timerId,
      stop: () => {
        stopped = true;
        activeNodes.forEach((node) => {
          try {
            node.stop();
          } catch {
            // Node may already have stopped naturally.
          }
        });
        activeNodes.clear();
        filter.disconnect();
        bus.disconnect();
      },
    };
  }

  private stopActiveTrack(fadeSeconds: number) {
    if (!this.context || !this.activeTrack) {
      return;
    }

    const track = this.activeTrack;
    const now = this.context.currentTime;

    window.clearInterval(track.timerId);
    track.bus.gain.cancelScheduledValues(now);
    track.bus.gain.setTargetAtTime(0.0001, now, Math.max(0.02, fadeSeconds / 4));
    window.setTimeout(track.stop, Math.max(100, fadeSeconds * 1000));
    this.activeTrack = null;
  }

  private schedulePad(
    startAt: number,
    duration: number,
    frequencies: number[],
    config: SceneConfig,
    output: AudioNode,
    activeNodes: Set<AudioScheduledSourceNode>,
  ) {
    if (!this.context) {
      return;
    }

    frequencies.forEach((frequency, index) => {
      const oscillator = this.context!.createOscillator();
      const gain = this.context!.createGain();

      oscillator.type = config.waveform;
      oscillator.frequency.value = frequency;
      oscillator.detune.value = index === 1 ? config.detune : -config.detune;
      gain.gain.setValueAtTime(0.0001, startAt);
      gain.gain.exponentialRampToValueAtTime(0.042, startAt + 1.2);
      gain.gain.setValueAtTime(0.042, startAt + Math.max(1.3, duration - 1.4));
      gain.gain.exponentialRampToValueAtTime(0.0001, startAt + duration);

      oscillator.connect(gain);
      gain.connect(output);
      oscillator.start(startAt);
      oscillator.stop(startAt + duration + 0.05);
      activeNodes.add(oscillator);
      oscillator.addEventListener("ended", () => {
        activeNodes.delete(oscillator);
        oscillator.disconnect();
        gain.disconnect();
      });
    });
  }

  private schedulePulsePattern(
    startAt: number,
    duration: number,
    bassFrequency: number,
    config: SceneConfig,
    output: AudioNode,
    activeNodes: Set<AudioScheduledSourceNode>,
  ) {
    if (!this.context) {
      return;
    }

    const beatSeconds = duration / 8;

    for (let index = 0; index < 8; index += 1) {
      const oscillator = this.context.createOscillator();
      const gain = this.context.createGain();
      const noteStart = startAt + index * beatSeconds;
      const frequency = index % 4 === 3 ? bassFrequency * 1.5 : bassFrequency;

      oscillator.type = config.pulseWaveform;
      oscillator.frequency.value = frequency;
      gain.gain.setValueAtTime(0.0001, noteStart);
      gain.gain.exponentialRampToValueAtTime(0.04, noteStart + 0.025);
      gain.gain.exponentialRampToValueAtTime(
        0.0001,
        noteStart + beatSeconds * 0.55,
      );

      oscillator.connect(gain);
      gain.connect(output);
      oscillator.start(noteStart);
      oscillator.stop(noteStart + beatSeconds * 0.6);
      activeNodes.add(oscillator);
      oscillator.addEventListener("ended", () => {
        activeNodes.delete(oscillator);
        oscillator.disconnect();
        gain.disconnect();
      });
    }
  }

  private playTone(
    startAt: number,
    frequency: number,
    duration: number,
    volume: number,
    waveform: OscillatorType,
    endFrequency = frequency,
  ) {
    if (!this.context || !this.effectsGain) {
      return;
    }

    const oscillator = this.context.createOscillator();
    const gain = this.context.createGain();

    oscillator.type = waveform;
    oscillator.frequency.setValueAtTime(frequency, startAt);
    oscillator.frequency.exponentialRampToValueAtTime(
      Math.max(1, endFrequency),
      startAt + duration,
    );
    gain.gain.setValueAtTime(0.0001, startAt);
    gain.gain.exponentialRampToValueAtTime(volume, startAt + 0.01);
    gain.gain.exponentialRampToValueAtTime(0.0001, startAt + duration);

    oscillator.connect(gain);
    gain.connect(this.effectsGain);
    oscillator.start(startAt);
    oscillator.stop(startAt + duration + 0.02);
  }

  private playNoiseSweep(
    startAt: number,
    duration: number,
    startFrequency: number,
    endFrequency: number,
    volume: number,
  ) {
    if (!this.context || !this.effectsGain) {
      return;
    }

    const frameCount = Math.ceil(this.context.sampleRate * duration);
    const buffer = this.context.createBuffer(
      1,
      frameCount,
      this.context.sampleRate,
    );
    const samples = buffer.getChannelData(0);

    for (let index = 0; index < frameCount; index += 1) {
      samples[index] = Math.random() * 2 - 1;
    }

    const source = this.context.createBufferSource();
    const filter = this.context.createBiquadFilter();
    const gain = this.context.createGain();

    source.buffer = buffer;
    filter.type = "bandpass";
    filter.frequency.setValueAtTime(startFrequency, startAt);
    filter.frequency.exponentialRampToValueAtTime(endFrequency, startAt + duration);
    filter.Q.value = 1.4;
    gain.gain.setValueAtTime(volume, startAt);
    gain.gain.exponentialRampToValueAtTime(0.0001, startAt + duration);

    source.connect(filter);
    filter.connect(gain);
    gain.connect(this.effectsGain);
    source.start(startAt);
    source.stop(startAt + duration);
  }
}

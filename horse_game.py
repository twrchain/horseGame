"""
Interactive horse-themed mini game built with tkinter.

Aligns with the brief: focuses on "马" + 创新/智能/创意 by mixing motion,
simple procedural "AI" hints, and a minimal code-based art style.
"""

import ctypes
import json
import math
import os
import random
import threading
import time
import tkinter as tk
from typing import List, Dict, Any


class HorseGame:
    def __init__(self) -> None:
        # 基础尺寸与物理参数
        self.width = 900
        self.height = 520
        self.ground_y = self.height - 90
        self.gravity = 2200.0
        self.jump_strength = 1100.0
        self.max_air_jumps = 1  # 空中额外可跳一次
        self.spawn_timer = 0.0
        # 场景状态
        self.obstacles: List[Dict[str, Any]] = []
        self.trails: List[Dict[str, float]] = []
        self.horse_img: tk.PhotoImage | None = None
        self.horse_jump_img: tk.PhotoImage | None = None
        self.horse_defend_img: tk.PhotoImage | None = None
        self.horse_sprite_size = (110.0, 70.0)
        self.fireworks: List[Dict[str, Any]] = []
        self.top_lanterns: List[Dict[str, float]] = []
        self.ground_anim_timer = 0.0  # 地面奔跑帧计时
        self.ground_anim_frame = 0    # 0/1 切换两张图
        self.air_stars: List[Dict[str, float]] = []  # 可收集的星星
        self.star_spawn_timer = 0.0  # 星星生成计时
        self.invincible_timer = 0.0  # 无敌剩余时间
        self.current_hint = ""
        self.hint_sound_cooldown = 0.0
        self.sound_lock = threading.Lock()
        self.jump_sound_counter = 0
        self.jump_prompt_played = False
        self.awaiting_start = True
        self.preparing_start = False
        self.countdown_timer = 0.0
        self.start_button_bounds = (0, 0, 0, 0)
        self.slide_timer = 0.0
        self.slide_cooldown = 0.0
        self.powerups: List[Dict[str, Any]] = []
        self.powerup_spawn_timer = 0.0
        self.slow_timer = 0.0
        self.magnet_timer = 0.0
        self.double_score_timer = 0.0
        self.shield = False
        self.total_stars = 0
        self.star_combo = 0
        self.star_combo_timer = 0.0
        self.achievements: set[str] = set()
        self.achievement_text = ""
        self.achievement_timer = 0.0
        self.mode = "endless"
        self.modes = ["endless", "challenge", "timed"]
        self.mode_labels = {"endless": "无尽", "challenge": "挑战", "timed": "计时"}
        self.time_limit = 60.0
        self.game_over_reason = ""
        self.paused = False
        self.difficulty = 1.0
        self.stage = 0
        self.records_path = os.path.join(os.path.dirname(__file__), "horse_records.json")
        self.records = self._load_records()
        self.bindings = {
            "jump": "space",
            "slide": "s",
            "pause": "Return",
            "reset": "r",
            "mode": "m",
            "volume": "v",
            "visual": "c",
            "rebind": "F2",
        }
        self.rebind_queue: List[str] = []
        self.rebind_active = False
        self.volume_levels = [0.0, 0.4, 0.7, 1.0]
        self.volume_index = 2
        self.volume = self.volume_levels[self.volume_index]
        self.visual_mode = 0
        self.visual_profiles = [
            {
                "sky": ["#22030a", "#3a0a14", "#530e19", "#6e111b", "#8a141b"],
                "ground": "#2b0a0f",
                "grid": "#5c1b21",
                "line": "#d4953f",
                "glow": "#ffce73",
            },
            {
                "sky": ["#05070f", "#0e1326", "#161d3b", "#1b274a", "#23335e"],
                "ground": "#0b0f1f",
                "grid": "#2a3864",
                "line": "#fcbf49",
                "glow": "#fef3c7",
            },
            {
                "sky": ["#1c0b12", "#2a0f18", "#36131d", "#421621", "#4e1a25"],
                "ground": "#250a12",
                "grid": "#4a1b27",
                "line": "#d4953f",
                "glow": "#f4d35e",
            },
        ]

        sound_dir = os.path.join(os.path.dirname(__file__), "image")
        self.sound_paths = {
            "start": os.path.join(sound_dir, "先试一试，空格起跳.MP3"),
            "jump": os.path.join(sound_dir, "轻盈跃起！.MP3"),
            "double_jump": os.path.join(sound_dir, "连跳加速！.MP3"),
            "pause": os.path.join(sound_dir, "暂停.MP3"),
            "resume": os.path.join(sound_dir, "继续冲刺.MP3"),
            "hit": os.path.join(sound_dir, "撞到障碍了，按 R 继续.MP3"),
            "invincible": os.path.join(sound_dir, "星光护体，5秒无敌！.MP3"),
            "hint_keep": os.path.join(sound_dir, "保持节奏.MP3"),
            "hint_ready": os.path.join(sound_dir, "准备跳！.MP3"),
            "hint_caution": os.path.join(sound_dir, "贴近了，小心！.MP3"),
            "hint_observe": os.path.join(sound_dir, "观察前方，寻找创造路.MP3"),
        }

        # 初始化窗口与事件绑定
        self.root = tk.Tk()
        self.root.title("小马蹦蹦跳")
        self.canvas = tk.Canvas(self.root, width=self.width, height=self.height, bg="#0d0f1a", highlightthickness=0)
        self.canvas.pack()

        self.canvas.focus_set()
        self.canvas.bind("<KeyPress>", self.handle_key_press)
        self.canvas.bind("<Button-1>", self.handle_click)

        self.load_horse_sprite()
        self.top_lanterns = self._make_top_lanterns()
        self.reset()
        self.last_time = time.time()
        self.tick()

    def load_horse_sprite(self) -> None:
        """加载奔跑与跳跃马的贴图，自动缩放。"""
        base_dir = os.path.join(os.path.dirname(__file__), "image")
        main_path = os.path.join(base_dir, "horse.png")
        jump_path = os.path.join(base_dir, "horse_jump.png")
        defend_path = os.path.join(base_dir, "horse_Defend.png")

        def load_scaled(path: str) -> tk.PhotoImage | None:
            try:
                img = tk.PhotoImage(file=path)
                target_w, target_h = 150.0, 110.0
                factor = max(img.width() / target_w, img.height() / target_h, 1.0)
                subsample = int(factor) if factor > 1 else 1
                return img.subsample(subsample) if subsample > 1 else img
            except Exception:
                return None

        main_sprite = load_scaled(main_path)
        jump_sprite = load_scaled(jump_path)
        defend_sprite = load_scaled(defend_path)

        self.horse_img = main_sprite
        self.horse_jump_img = jump_sprite
        self.horse_defend_img = defend_sprite
        if self.horse_img:
            self.horse_sprite_size = (float(self.horse_img.width()), float(self.horse_img.height()))
        else:
            self.horse_sprite_size = (110.0, 70.0)

    def _load_records(self) -> Dict[str, Any]:
        default = {
            "best_time": 0.0,
            "best_distance": 0.0,
            "best_score": 0,
            "best_combo": 0,
            "best_timed_score": 0,
            "best_challenge_time": 0.0,
        }
        if not os.path.exists(self.records_path):
            return default
        try:
            with open(self.records_path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            if not isinstance(data, dict):
                return default
            merged = default.copy()
            merged.update({k: data.get(k, v) for k, v in default.items()})
            return merged
        except Exception:
            return default

    def _save_records(self) -> None:
        try:
            with open(self.records_path, "w", encoding="utf-8") as handle:
                json.dump(self.records, handle, ensure_ascii=True, indent=2)
        except Exception:
            pass

    def _normalize_key(self, keysym: str) -> str:
        return keysym.lower() if len(keysym) == 1 else keysym

    def handle_click(self, event=None) -> None:
        if event is None:
            return
        if self.awaiting_start and not self.preparing_start:
            x1, y1, x2, y2 = self.start_button_bounds
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                self.preparing_start = True
                self.countdown_timer = 3.0
                self.status_text = "陈思颖: 准备起跑！"

    def _play_sound(self, path: str) -> None:
        """异步播放 MP3 音效（使用 winmm mci）。"""
        if not path or not os.path.exists(path) or self.volume <= 0:
            return
        abs_path = os.path.abspath(path)
        volume_value = int(self.volume * 1000)

        def _worker() -> None:
            alias = f"snd{int(time.time() * 1000)}{random.randint(0, 9999)}"
            mci = ctypes.windll.winmm.mciSendStringW
            with self.sound_lock:
                mci(f'open "{abs_path}" type mpegvideo alias {alias}', None, 0, None)
                mci(f"setaudio {alias} volume to {volume_value}", None, 0, None)
                mci(f"play {alias} wait", None, 0, None)
                mci(f"close {alias}", None, 0, None)

        threading.Thread(target=_worker, daemon=True).start()

    def _play_sound_key(self, key: str) -> None:
        path = self.sound_paths.get(key, "")
        self._play_sound(path)

    def _stop_all_sounds(self) -> None:
        """停止所有正在播放的音效。"""
        ctypes.windll.winmm.mciSendStringW("close all", None, 0, None)

    def _make_top_lanterns(self) -> List[Dict[str, float]]:
        """生成顶部左右对称的灯笼坐标。"""
        lanterns: List[Dict[str, float]] = []
        center = self.width / 2
        offsets = [180, 270, 360]
        sizes = [random.uniform(34, 54) for _ in offsets]
        ys = [random.uniform(32, 46) for _ in offsets]
        blessings = ["福", "春", "吉祥", "如意", "安康", "平安", "顺意", "招财"]
        for off, size, y in zip(offsets, sizes, ys):
            label = random.choice(blessings)
            lanterns.append({"x": center - off, "y": y, "size": size, "label": label})
            lanterns.append({"x": center + off, "y": y, "size": size, "label": label})
        # Sort left to right for consistent drawing.
        lanterns.sort(key=lambda l: l["x"])
        return lanterns

    def _make_challenge_pattern(self) -> List[Dict[str, Any]]:
        """固定挑战关卡序列。"""
        pattern = []
        base_delay = 1.1
        themes = ["fence", "data", "lantern", "light"]
        for i in range(12):
            pattern.append(
                {
                    "delay": base_delay + i * 0.15,
                    "h": 70 + i * 3,
                    "w": 50 + (i % 3) * 10,
                    "speed": 260 + i * 12,
                    "theme": themes[i % len(themes)],
                    "label": random.choice(["勇", "智", "行", "跃", "创", "新"]),
                }
            )
        return pattern

    def reset(self) -> None:
        """重置游戏到初始状态。"""
        w, h = self.horse_sprite_size
        self.horse = {
            "x": 120.0,
            "y": self.ground_y - h,
            "w": w,
            "h": h,
            "vy": 0.0,
            "on_ground": True,
        }
        self.obstacles.clear()
        self.trails.clear()
        self.fireworks.clear()
        self.air_stars.clear()
        self.powerups.clear()
        self.spawn_timer = 1.2
        self.star_spawn_timer = 0.8
        self.powerup_spawn_timer = 1.6
        self.running = False
        self.paused = False
        self.awaiting_start = True
        self.preparing_start = False
        self.countdown_timer = 0.0
        self.start_button_bounds = (0, 0, 0, 0)
        self.game_over_reason = ""
        self.start_time = time.time()
        self.elapsed = 0.0
        self.jumps = 0
        self.air_jumps_used = 0
        self.score = 0
        self.total_stars = 0
        self.star_combo = 0
        self.star_combo_timer = 0.0
        self.invincible_timer = 0.0
        self.slow_timer = 0.0
        self.magnet_timer = 0.0
        self.double_score_timer = 0.0
        self.shield = False
        self.distance = 0.0
        self.slide_timer = 0.0
        self.slide_cooldown = 0.0
        self.status_text = f"陈思颖: {self.mode_labels[self.mode]}模式，空格起跳"
        self.ground_anim_timer = 0.0
        self.ground_anim_frame = 0
        self.current_hint = ""
        self.hint_sound_cooldown = 0.0
        self.jump_sound_counter = 0
        self.jump_prompt_played = False
        self.hint_trigger_counter = 0
        self.caution_trigger_counter = 0
        self.achievements.clear()
        self.achievement_text = ""
        self.achievement_timer = 0.0
        self.difficulty = 1.0
        self.stage = 0
        self.challenge_pattern = self._make_challenge_pattern()
        self.challenge_index = 0
        self.challenge_timer = self.challenge_pattern[0]["delay"] if self.challenge_pattern else 1.0
        self._stop_all_sounds()
        self._play_sound_key("start")

    def handle_key_press(self, event=None) -> None:
        """统一按键入口，支持改键与多操作。"""
        if event is None:
            return
        key = self._normalize_key(event.keysym)
        if self.rebind_active:
            action = self.rebind_queue.pop(0)
            self.bindings[action] = key
            if self.rebind_queue:
                next_action = self.rebind_queue[0]
                self.status_text = f"陈思颖: 请按新的 {next_action} 键"
            else:
                self.rebind_active = False
                self.status_text = "陈思颖: 改键完成！"
            return

        if key == self.bindings["rebind"]:
            self.rebind_queue = ["jump", "slide", "pause", "reset", "mode", "volume", "visual"]
            self.rebind_active = True
            self.status_text = "陈思颖: 请按新的 jump 键"
            return

        if key == self.bindings["volume"]:
            self.toggle_volume()
            return
        if key == self.bindings["visual"]:
            self.cycle_visual_mode()
            return
        if key == self.bindings["mode"]:
            self.cycle_mode()
            return

        if key == self.bindings["pause"]:
            if self.awaiting_start and not self.preparing_start:
                self.preparing_start = True
                self.countdown_timer = 3.0
                self.status_text = "陈思颖: 准备起跑！"
                return
            self.toggle_pause()
            return
        if key == self.bindings["reset"]:
            self.handle_reset()
            return

        if not self.running or self.paused:
            return

        if key == self.bindings["slide"]:
            self.handle_slide()
            return
        if key == self.bindings["jump"]:
            if self.horse["on_ground"]:
                self._do_jump(self.jump_strength, air_jump=False)
            else:
                if self.air_jumps_used < self.max_air_jumps:
                    self._do_jump(self.jump_strength, air_jump=True)

    def _do_jump(self, strength: float, air_jump: bool) -> None:
        """执行跳跃动作。"""
        self.horse["vy"] = -strength
        self.horse["on_ground"] = False
        if air_jump:
            self.air_jumps_used += 1
        else:
            self.air_jumps_used = 0
        self.jumps += 1
        if air_jump:
            self.status_text = "陈思颖: 连跳加速！"
            self.jump_sound_counter += 1
            if self.jump_sound_counter % 6 == 0:
                self._play_sound_key("double_jump")
        else:
            self.status_text = "陈思颖: 轻盈跃起！"
            if not self.jump_prompt_played:
                self._play_sound_key("jump")
                self.jump_prompt_played = True

    def handle_reset(self, event=None) -> None:
        """按 R 重置。"""
        self.reset()

    def toggle_pause(self, event=None) -> None:
        """暂停/继续。"""
        if not self.running or self.awaiting_start or self.preparing_start:
            return
        self.paused = not self.paused
        self.status_text = "陈思颖: 暂停" if self.paused else "陈思颖: 继续冲刺"
        self._play_sound_key("pause" if self.paused else "resume")

    def toggle_volume(self) -> None:
        self.volume_index = (self.volume_index + 1) % len(self.volume_levels)
        self.volume = self.volume_levels[self.volume_index]
        label = "静音" if self.volume == 0 else f"{int(self.volume * 100)}%"
        self.status_text = f"陈思颖: 音量 {label}"

    def cycle_visual_mode(self) -> None:
        self.visual_mode = (self.visual_mode + 1) % len(self.visual_profiles)
        label = ["霓红", "高对比", "低闪烁"][self.visual_mode]
        self.status_text = f"陈思颖: 画面 {label}"

    def cycle_mode(self) -> None:
        if self.running and not self.paused:
            return
        index = self.modes.index(self.mode)
        self.mode = self.modes[(index + 1) % len(self.modes)]
        self.status_text = f"陈思颖: 切换到 {self.mode_labels[self.mode]}"
        self.reset()

    def handle_slide(self) -> None:
        if not self.horse["on_ground"] or self.slide_cooldown > 0:
            return
        self.slide_timer = 0.45
        self.slide_cooldown = 1.3
        self.status_text = "陈思颖: 滑行闪避！"

    def spawn_obstacle(self, config: Dict[str, Any] | None = None) -> None:
        """生成障碍，附带一个祝福词。"""
        if config:
            height = int(config["h"])
            width = int(config["w"])
            speed = float(config["speed"])
            theme = config.get("theme", "fence")
            blessing = config.get("label", "福")
        else:
            scale = 0.8 + self.difficulty * 0.35
            height = int(random.randint(60, 120) * (0.9 + self.difficulty * 0.1))
            width = int(random.randint(40, 80) * (0.9 + self.difficulty * 0.08))
            speed = random.randint(230, 360) * scale
            theme = random.choice(["data", "fence", "light", "lantern"])
            blessing = random.choice(["福", "春", "安康", "平安", "顺意", "如意"])
        self.obstacles.append(
            {
                "x": self.width + 20.0,
                "y": self.ground_y - height,
                "w": float(width),
                "h": float(height),
                "speed": float(speed),
                "theme": theme,
                "label": blessing,
            }
        )
        if not config:
            self.spawn_timer = random.uniform(1.1, 2.1) / max(0.8, self.difficulty)

    def update_horse(self, dt: float) -> None:
        """更新马的物理位置与落地状态。"""
        self.horse["vy"] += self.gravity * dt
        self.horse["y"] += self.horse["vy"] * dt

        if self.horse["y"] >= self.ground_y - self.horse["h"]:
            self.horse["y"] = self.ground_y - self.horse["h"]
            self.horse["vy"] = 0.0
            self.horse["on_ground"] = True
            self.air_jumps_used = 0
        else:
            self.horse["on_ground"] = False


    def world_speed_multiplier(self) -> float:
        mul = self.difficulty
        if self.invincible_timer > 0:
            mul *= 1.35
        if self.slow_timer > 0:
            mul *= 0.6
        return max(0.4, min(mul, 3.0))

    def update_obstacles(self, dt: float) -> None:
        """推进障碍并清理离场。"""
        speed_mul = self.world_speed_multiplier()
        for obs in self.obstacles:
            obs["x"] -= obs["speed"] * dt * speed_mul
        self.obstacles = [o for o in self.obstacles if o["x"] + o["w"] > -30]

    def spawn_firework(self) -> None:
        """生成一束烟花粒子。"""
        x = random.uniform(120, self.width - 120)
        y = random.uniform(80, self.height * 0.4)
        count = random.randint(15, 24)
        particles = []
        for _ in range(count):
            angle = random.uniform(0, 3.1415 * 2)
            speed = random.uniform(90, 210)
            vx = speed * math.cos(angle)
            vy = speed * math.sin(angle)
            particles.append({"x": x, "y": y, "vx": vx, "vy": vy, "life": random.uniform(0.8, 1.4)})
        color = random.choice(["#ff4d4f", "#ffd166", "#ff7a45", "#ff3859"])
        self.fireworks.append({"particles": particles, "color": color})

    def spawn_star(self) -> None:
        """生成可收集星星。"""
        x = self.width + 30
        y = random.uniform(120, self.ground_y - 120)
        size = random.uniform(10, 16)
        self.air_stars.append(
            {"x": x, "y": y, "size": size, "speed": random.uniform(220, 320)}
        )

    def spawn_powerup(self) -> None:
        """生成道具。"""
        x = self.width + 40
        y = random.uniform(140, self.ground_y - 140)
        kind = random.choice(["slow", "shield", "magnet", "double"])
        self.powerups.append({"x": x, "y": y, "size": 16.0, "speed": random.uniform(200, 300), "kind": kind})

    def apply_powerup(self, kind: str) -> None:
        if kind == "slow":
            self.slow_timer = 4.0
            self.status_text = "陈思颖: 时空减速！"
        elif kind == "shield":
            self.shield = True
            self.status_text = "陈思颖: 护盾就位！"
        elif kind == "magnet":
            self.magnet_timer = 6.0
            self.status_text = "陈思颖: 星星磁吸！"
        elif kind == "double":
            self.double_score_timer = 6.0
            self.status_text = "陈思颖: 星星翻倍！"

    def update_powerups(self, dt: float) -> None:
        speed_mul = self.world_speed_multiplier()
        for p in self.powerups:
            p["x"] -= p["speed"] * dt * speed_mul
        self.powerups = [p for p in self.powerups if p["x"] > -50]

    def update_fireworks(self, dt: float) -> None:
        """更新烟花粒子运动与存活。"""
        spawn_rate = 0.02 if self.visual_mode != 2 else 0.006
        if random.random() < spawn_rate:
            self.spawn_firework()
        alive = []
        for fw in self.fireworks:
            particles = []
            for p in fw["particles"]:
                p["x"] += p["vx"] * dt
                p["y"] += p["vy"] * dt
                p["vy"] += 220 * dt
                p["life"] -= dt
                if p["life"] > 0:
                    particles.append(p)
            if particles:
                fw["particles"] = particles
                alive.append(fw)
        self.fireworks = alive

    def update_air_stars(self, dt: float) -> None:
        """更新可收集星星。"""
        speed_mul = self.world_speed_multiplier()
        hx = self.horse["x"] + self.horse["w"] * 0.5
        hy = self.horse["y"] + self.horse["h"] * 0.5
        for s in self.air_stars:
            s["x"] -= s["speed"] * dt * speed_mul
            if self.magnet_timer > 0:
                dx = hx - s["x"]
                dy = hy - s["y"]
                dist = math.hypot(dx, dy) + 0.01
                pull = 260 * dt
                s["x"] += dx / dist * pull
                s["y"] += dy / dist * pull
        self.air_stars = [s for s in self.air_stars if s["x"] > -40]

    def check_collisions(self) -> None:
        """检测马与障碍的碰撞。"""
        hx, hy, hw, hh = self.horse["x"], self.horse["y"], self.horse["w"], self.horse["h"]
        hit_h = hh * (0.6 if self.slide_timer > 0 else 1.0)
        hit_y = hy + (hh - hit_h)
        invulnerable = self.invincible_timer > 0
        if not invulnerable:
            for obs in self.obstacles:
                ox, oy, ow, oh = obs["x"], obs["y"], obs["w"], obs["h"]
                if hx < ox + ow and hx + hw > ox and hit_y < oy + oh and hit_y + hit_h > oy:
                    if self.shield:
                        self.shield = False
                        self.invincible_timer = max(self.invincible_timer, 1.2)
                        self.status_text = "陈思颖: 护盾破碎！"
                        return
                    self._end_game("hit")
                    return

        # 收集星星加分
        collected = []
        for s in self.air_stars:
            sx, sy, ss = s["x"], s["y"], s["size"]
            if hx < sx + ss and hx + hw > sx - ss and hit_y < sy + ss and hit_y + hit_h > sy - ss:
                collected.append(s)
        if collected:
            for s in collected:
                self.air_stars.remove(s)
            score_gain = len(collected) * (2 if self.double_score_timer > 0 else 1)
            self.score += score_gain
            self.total_stars += len(collected)
            self.star_combo += len(collected)
            self.star_combo_timer = 1.8
            if self.score >= 10:
                self.score = 0
                self.invincible_timer = 5.0
                self.status_text = "陈思颖: 星光护体，5秒无敌！"
                self._play_sound_key("invincible")
            if self.total_stars >= 10:
                self._set_achievement("十星初成")
            if self.star_combo >= 5:
                self._set_achievement("星光连击")

        collected_powerups = []
        for p in self.powerups:
            px, py, ps = p["x"], p["y"], p["size"]
            if hx < px + ps and hx + hw > px - ps and hit_y < py + ps and hit_y + hit_h > py - ps:
                collected_powerups.append(p)
        if collected_powerups:
            for p in collected_powerups:
                self.powerups.remove(p)
                self.apply_powerup(p["kind"])

    def _set_achievement(self, title: str) -> None:
        if title in self.achievements:
            return
        self.achievements.add(title)
        self.achievement_text = f"成就达成: {title}"
        self.achievement_timer = 2.6

    def _end_game(self, reason: str) -> None:
        self.running = False
        self.game_over_reason = reason
        self._update_records()
        self._stop_all_sounds()
        if reason == "hit":
            self.status_text = "陈思颖: 撞到障碍了，按 R 继续"
            self._play_sound_key("hit")
        elif reason == "challenge":
            self.status_text = "陈思颖: 挑战完成！"
        elif reason == "timed":
            self.status_text = "陈思颖: 计时完成！"
        else:
            self.status_text = "陈思颖: 本局结束"

    def _update_records(self) -> None:
        if self.elapsed > self.records["best_time"]:
            self.records["best_time"] = self.elapsed
        if self.distance > self.records["best_distance"]:
            self.records["best_distance"] = self.distance
        if self.total_stars > self.records["best_score"]:
            self.records["best_score"] = self.total_stars
        if self.star_combo > self.records["best_combo"]:
            self.records["best_combo"] = self.star_combo
        if self.mode == "timed" and self.total_stars > self.records["best_timed_score"]:
            self.records["best_timed_score"] = self.total_stars
        if self.mode == "challenge":
            if self.game_over_reason == "challenge":
                if self.records["best_challenge_time"] == 0 or self.elapsed < self.records["best_challenge_time"]:
                    self.records["best_challenge_time"] = self.elapsed
        self._save_records()

    def nearest_hint(self) -> str:
        """AI 提示：基于最近障碍给出文案。"""
        hx = self.horse["x"] + self.horse["w"]
        ahead = [o for o in self.obstacles if o["x"] + o["w"] >= hx]
        if not ahead:
            return "陈思颖: 保持节奏"
        nearest = min(ahead, key=lambda o: o["x"])
        distance = nearest["x"] - hx
        if distance < 60:
            return "陈思颖: 贴近了，小心！"
        if self.horse["on_ground"] and distance < 220:
            return "陈思颖: 准备跳！"
        return "陈思颖: 观察前方，寻找创造路"

    def draw_background(self) -> None:
        profile = self.visual_profiles[self.visual_mode]
        gradient_colors = profile["sky"]
        band_h = self.height / len(gradient_colors)
        for i, color in enumerate(gradient_colors):
            self.canvas.create_rectangle(0, i * band_h, self.width, (i + 1) * band_h, fill=color, outline="")

        # Ground strip with subtle gold grid.
        self.canvas.create_rectangle(0, self.ground_y, self.width, self.height, fill=profile["ground"], outline="")
        for x in range(0, self.width + 1, 50):
            self.canvas.create_line(x, self.ground_y, x - 40, self.height, fill=profile["grid"], width=1)
        self.canvas.create_line(0, self.ground_y, self.width, self.ground_y, fill=profile["line"], width=3)
        for x in range(20, self.width, 40):
            self.canvas.create_oval(x - 2, self.ground_y + 10, x + 2, self.ground_y + 14, fill=profile["glow"], outline="")

    def draw_top_lanterns(self) -> None:
        """顶部绳子 + 对称灯笼 + 中心祝福文字。"""
        rope_y = 26
        self.canvas.create_line(14, rope_y, self.width / 2 - 90, rope_y, fill="#fcbf49", width=3, smooth=True)
        self.canvas.create_line(self.width / 2 + 90, rope_y, self.width - 14, rope_y, fill="#fcbf49", width=3, smooth=True)
        self.canvas.create_text(
            self.width / 2,
            rope_y + 2,
            text="新年快乐",
            fill="#ffd166",
            font=("SimSun", 26, "bold"),
        )
        for lantern in self.top_lanterns:
            x = lantern["x"]
            y = lantern["y"]
            size = lantern["size"]
            label = lantern.get("label", "")
            w = size * 1.15
            h = size
            self.canvas.create_oval(x - w / 2, y - h / 2, x + w / 2, y + h / 2, fill="#e63946", outline="#a4161a", width=3)
            self.canvas.create_rectangle(x - 6, y - h / 2 - 6, x + 6, y - h / 2 + 6, fill="#ffb703", outline="")
            self.canvas.create_line(x, y + h / 2, x, y + h / 2 + 16, fill="#fcbf49", width=3)
            if label:
                self.canvas.create_text(
                    x,
                    y,
                    text=label,
                    fill="#ffe8d6",
                    font=("SimSun", int(min(18, max(12, h * 0.45))), "bold"),
                )

    def draw_fireworks(self) -> None:
        """绘制烟花粒子。"""
        for fw in self.fireworks:
            color = fw["color"]
            for p in fw["particles"]:
                alpha = max(0.2, p["life"])
                size = max(2, 5 * p["life"])
                self.canvas.create_oval(
                    p["x"] - size,
                    p["y"] - size,
                    p["x"] + size,
                    p["y"] + size,
                    fill=color,
                    outline="",
                )

    def draw_air_stars(self) -> None:
        """绘制可收集星星。"""
        for s in self.air_stars:
            size = s["size"]
            x = s["x"]
            y = s["y"]
            points = []
            for i in range(5):
                angle = (i * 72 - 90) * math.pi / 180
                outer_x = x + math.cos(angle) * size
                outer_y = y + math.sin(angle) * size
                inner_angle = angle + 36 * math.pi / 180
                inner_x = x + math.cos(inner_angle) * size * 0.45
                inner_y = y + math.sin(inner_angle) * size * 0.45
                points.extend([outer_x, outer_y, inner_x, inner_y])
            self.canvas.create_polygon(points, fill="#fff3b0", outline="")

    def draw_powerups(self) -> None:
        """绘制道具。"""
        style = {
            "slow": ("#7bdff2", "慢"),
            "shield": ("#80ed99", "盾"),
            "magnet": ("#f4acb7", "吸"),
            "double": ("#f9c74f", "倍"),
        }
        for p in self.powerups:
            color, label = style.get(p["kind"], ("#ffffff", "?"))
            size = p["size"]
            x = p["x"]
            y = p["y"]
            self.canvas.create_oval(x - size, y - size, x + size, y + size, fill=color, outline="")
            self.canvas.create_text(x, y, text=label, fill="#1a1a1a", font=("SimSun", 10, "bold"))

    def draw_horse(self) -> None:
        """绘制马（落地/空中分别用不同贴图）。"""
        x, y, w, h = self.horse["x"], self.horse["y"], self.horse["w"], self.horse["h"]
        sprite = None
        if self.invincible_timer > 0 and self.horse_defend_img:
            sprite = self.horse_defend_img
        elif self.horse_img and self.horse_jump_img and self.horse["on_ground"]:
            sprite = self.horse_jump_img if self.ground_anim_frame else self.horse_img
        elif not self.horse["on_ground"] and self.horse_jump_img:
            sprite = self.horse_jump_img
        elif self.horse_img:
            sprite = self.horse_img

        if sprite:
            self.canvas.create_image(x, y, anchor="nw", image=sprite)
        else:
            body_color = "#f2c14f"
            accent = "#f77f00"
            self.canvas.create_rectangle(x, y + h * 0.25, x + w * 0.75, y + h * 0.85, fill=body_color, outline="")
            self.canvas.create_rectangle(x + w * 0.7, y + h * 0.2, x + w, y + h * 0.55, fill=body_color, outline="")
            self.canvas.create_polygon(
                x + w * 0.55,
                y + h * 0.2,
                x + w * 0.8,
                y + h * 0.05,
                x + w * 0.65,
                y + h * 0.2,
                fill=accent,
                outline="",
            )
            leg_w = w * 0.12
            for i, offset in enumerate([0.18, 0.38, 0.6, 0.8]):
                lx = x + w * offset
                swing = (i % 2) * 6 if not self.horse["on_ground"] else 0
                self.canvas.create_rectangle(
                    lx,
                    y + h * 0.8,
                    lx + leg_w,
                    y + h + swing,
                    fill="#cfa248",
                    outline="",
                )
            self.canvas.create_oval(
                x + w * 0.82,
                y + h * 0.3,
                x + w * 0.88,
                y + h * 0.36,
                fill="#0c0c0c",
                outline="",
            )

        if self.shield:
            self.canvas.create_oval(x - 6, y - 6, x + w + 6, y + h + 6, outline="#80ed99", width=2)

    def draw_obstacles(self) -> None:
        """绘制障碍与其祝福文字。"""
        for obs in self.obstacles:
            x, y, w, h = obs["x"], obs["y"], obs["w"], obs["h"]
            if obs["theme"] == "fence":
                self.canvas.create_rectangle(x, y, x + w, y + h, fill="#d9d9d9", outline="#bfbfbf", width=2)
                for bar in range(3):
                    yy = y + h * (bar + 1) / 4
                    self.canvas.create_line(x, yy, x + w, yy, fill="#8c8c8c", width=2)
            elif obs["theme"] == "data":
                self.canvas.create_rectangle(x, y, x + w, y + h, fill="#3bd8c0", outline="#0c7c6a", width=2)
                self.canvas.create_text(x + w / 2, y + h / 2, text="01", fill="#0a2d24", font=("SimSun", 12, "bold"))
            elif obs["theme"] == "lantern":
                self.canvas.create_oval(x, y, x + w, y + h, fill="#e63946", outline="#a4161a", width=3)
                self.canvas.create_rectangle(x + w * 0.45, y - 10, x + w * 0.55, y + 8, fill="#ffb703", outline="")
                self.canvas.create_line(x + w / 2, y + h, x + w / 2, y + h + 18, fill="#fcbf49", width=3)
            else:
                self.canvas.create_rectangle(x, y, x + w, y + h, fill="#f45b69", outline="#c73a47", width=2)
                self.canvas.create_polygon(
                    x + w / 2,
                    y - 14,
                    x + w * 0.2,
                    y,
                    x + w * 0.8,
                    y,
                    fill="#f9a23d",
                    outline="",
                )
            # Blessing text overlay.
            label = obs.get("label")
            if label:
                self.canvas.create_text(
                    x + w / 2,
                    y + h / 2,
                    text=label,
                    fill="#ffe8d6" if obs["theme"] != "data" else "#0c2a26",
                    font=("SimSun", int(min(18, max(12, h * 0.4))), "bold"),
                )

    def draw_hud(self) -> None:
        """绘制 HUD 文本。"""
        time_label = f"{self.elapsed:05.2f}s"
        if self.mode == "timed":
            remaining = max(0.0, self.time_limit - self.elapsed)
            time_label = f"{remaining:05.2f}s"
        stats = (
            f"{self.mode_labels[self.mode]}  时间 {time_label}  跃起 {self.jumps}  星星 {self.total_stars}  距离 {self.distance:05.1f}"
        )
        self.canvas.create_text(20, 110, anchor="nw", text=stats, fill="#f9f6f2", font=("SimSun", 12, "bold"))

        if self.mode == "timed":
            best = f"最佳 计时星星 {self.records['best_timed_score']}  距离 {self.records['best_distance']:.1f}"
        elif self.mode == "challenge":
            best_time = self.records["best_challenge_time"]
            label = f"{best_time:.1f}s" if best_time > 0 else "--"
            best = f"最佳 挑战用时 {label}  星星 {self.records['best_score']}"
        else:
            best = (
                f"最佳 时间 {self.records['best_time']:.1f}s  星星 {self.records['best_score']}  距离 {self.records['best_distance']:.1f}"
            )
        self.canvas.create_text(20, 132, anchor="nw", text=best, fill="#ffe8b3", font=("SimSun", 10))

        controls = "空格=起跳  S=滑行  M=模式  C=画面  V=音量  F2=改键"
        self.canvas.create_text(20, 150, anchor="nw", text=controls, fill="#ffe8b3", font=("SimSun", 10))

        effects = []
        if self.invincible_timer > 0:
            effects.append(f"无敌 {self.invincible_timer:0.1f}s")
        if self.slow_timer > 0:
            effects.append(f"减速 {self.slow_timer:0.1f}s")
        if self.magnet_timer > 0:
            effects.append(f"磁吸 {self.magnet_timer:0.1f}s")
        if self.double_score_timer > 0:
            effects.append(f"翻倍 {self.double_score_timer:0.1f}s")
        if self.shield:
            effects.append("护盾")
        if effects:
            self.canvas.create_text(20, 168, anchor="nw", text=" | ".join(effects), fill="#d9e2ff", font=("SimSun", 10))

        self.canvas.create_text(
            self.width - 20,
            96,
            anchor="ne",
            text=self.status_text,
            fill="#ffe8b3",
            font=("SimSun", 12, "bold"),
        )
        self.canvas.create_text(
            self.width - 20,
            120,
            anchor="ne",
            text=self.current_hint,
            fill="#fef3c7",
            font=("SimSun", 11),
        )
        if self.achievement_timer > 0:
            self.canvas.create_text(
                self.width - 20,
                144,
                anchor="ne",
                text=self.achievement_text,
                fill="#f4d35e",
                font=("SimSun", 11, "bold"),
            )

        if (self.awaiting_start or self.preparing_start) and not self.running:
            self.canvas.create_rectangle(
                self.width / 2 - 200,
                self.height / 2 - 100,
                self.width / 2 + 200,
                self.height / 2 + 100,
                fill="#0b0f1f",
                outline="#4fd1c5",
                width=3,
            )
            self.canvas.create_text(
                self.width / 2,
                self.height / 2 - 40,
                text="准备就绪再出发",
                fill="#ffd166",
                font=("SimSun", 16, "bold"),
            )
            if self.preparing_start:
                self.canvas.create_text(
                    self.width / 2,
                    self.height / 2,
                    text=f"{int(math.ceil(self.countdown_timer))}",
                    fill="#f9f6f2",
                    font=("SimSun", 36, "bold"),
                )
                self.start_button_bounds = (0, 0, 0, 0)
            else:
                btn_w, btn_h = 160, 44
                x1 = self.width / 2 - btn_w / 2
                y1 = self.height / 2 - btn_h / 2 + 10
                x2 = x1 + btn_w
                y2 = y1 + btn_h
                self.start_button_bounds = (x1, y1, x2, y2)
                self.canvas.create_rectangle(x1, y1, x2, y2, fill="#4fd1c5", outline="")
                self.canvas.create_text(
                    self.width / 2,
                    y1 + btn_h / 2,
                    text="点击开始",
                    fill="#0b0f1f",
                    font=("SimSun", 14, "bold"),
                )
        elif not self.running or self.paused:
            self.canvas.create_rectangle(
                self.width / 2 - 160,
                self.height / 2 - 80,
                self.width / 2 + 160,
                self.height / 2 + 80,
                fill="#0b0f1f",
                outline="#4fd1c5",
                width=3,
            )
            if self.paused:
                title = "暂停中"
                subtitle = "Enter 继续 · M 切模式 · R 重置"
                color = "#ffd166"
            else:
                if self.game_over_reason == "challenge":
                    title = "挑战完成！"
                    subtitle = "M 切模式 · R 重置"
                    color = "#80ed99"
                elif self.game_over_reason == "timed":
                    title = "计时完成！"
                    subtitle = "M 切模式 · R 重置"
                    color = "#80ed99"
                else:
                    title = "碰撞了，再试一次！"
                    subtitle = "R 重置 · 空格跳跃 · Enter 继续"
                    color = "#f45b69"
            self.canvas.create_text(
                self.width / 2,
                self.height / 2 - 10,
                text=title,
                fill=color,
                font=("SimSun", 16, "bold"),
            )
            self.canvas.create_text(
                self.width / 2,
                self.height / 2 + 26,
                text=subtitle,
                fill="#d9e2ff",
                font=("SimSun", 12),
            )

    def tick(self) -> None:
        """主循环：更新状态并重绘。"""
        now = time.time()
        dt = min(0.05, now - self.last_time)
        self.last_time = now

        if self.preparing_start:
            self.countdown_timer = max(0.0, self.countdown_timer - dt)
            if self.countdown_timer <= 0:
                self.preparing_start = False
                self.awaiting_start = False
                self.running = True
                self.start_time = time.time()
                self.status_text = "陈思颖: 起跑！"
        if self.running and not self.paused:
            self.elapsed = now - self.start_time
            if self.mode != "challenge":
                self.difficulty = 1.0 + min(self.elapsed / 38.0, 2.2)
            else:
                self.difficulty = 1.0
            new_stage = int(self.elapsed // 20)
            if self.mode != "challenge" and new_stage > self.stage:
                self.stage = new_stage
                self.status_text = "陈思颖: 节奏升级！"
            speed_mul = self.world_speed_multiplier()
            self.distance += dt * 6.5 * speed_mul

            if self.mode == "challenge":
                self.challenge_timer -= dt
                if self.challenge_index < len(self.challenge_pattern) and self.challenge_timer <= 0:
                    config = self.challenge_pattern[self.challenge_index]
                    self.spawn_obstacle(config)
                    self.challenge_index += 1
                    if self.challenge_index < len(self.challenge_pattern):
                        self.challenge_timer = self.challenge_pattern[self.challenge_index]["delay"]
            else:
                self.spawn_timer -= dt
                if self.spawn_timer <= 0:
                    self.spawn_obstacle()

            self.star_spawn_timer -= dt
            if self.star_spawn_timer <= 0:
                self.spawn_star()
                self.star_spawn_timer = random.uniform(0.7, 1.3)

            self.powerup_spawn_timer -= dt
            if self.powerup_spawn_timer <= 0:
                self.spawn_powerup()
                self.powerup_spawn_timer = random.uniform(4.0, 6.5)

            self.update_horse(dt)
            self.update_obstacles(dt)
            self.update_fireworks(dt)
            self.update_air_stars(dt)
            self.update_powerups(dt)
            self.check_collisions()

            if self.invincible_timer > 0:
                self.invincible_timer = max(0.0, self.invincible_timer - dt)
            if self.slow_timer > 0:
                self.slow_timer = max(0.0, self.slow_timer - dt)
            if self.magnet_timer > 0:
                self.magnet_timer = max(0.0, self.magnet_timer - dt)
            if self.double_score_timer > 0:
                self.double_score_timer = max(0.0, self.double_score_timer - dt)
            if self.slide_timer > 0:
                self.slide_timer = max(0.0, self.slide_timer - dt)
            if self.slide_cooldown > 0:
                self.slide_cooldown = max(0.0, self.slide_cooldown - dt)
            if self.star_combo_timer > 0:
                self.star_combo_timer = max(0.0, self.star_combo_timer - dt)
                if self.star_combo_timer == 0:
                    self.star_combo = 0
            if self.achievement_timer > 0:
                self.achievement_timer = max(0.0, self.achievement_timer - dt)
            if self.hint_sound_cooldown > 0:
                self.hint_sound_cooldown = max(0.0, self.hint_sound_cooldown - dt)

            if self.jumps >= 15:
                self._set_achievement("连跳达人")
            if self.elapsed >= 30:
                self._set_achievement("无伤30秒")

            if self.mode == "timed" and self.elapsed >= self.time_limit:
                self._set_achievement("计时胜利")
                self._end_game("timed")
            if self.mode == "challenge" and self.challenge_index >= len(self.challenge_pattern) and not self.obstacles:
                self._set_achievement("挑战通关")
                self._end_game("challenge")

            new_hint = self.nearest_hint()
            if new_hint != self.current_hint:
                self.current_hint = new_hint
                hint_map = {
                    "陈思颖: 保持节奏": "hint_keep",
                    "陈思颖: 准备跳！": "hint_ready",
                    "陈思颖: 贴近了，小心！": "hint_caution",
                    "陈思颖: 观察前方，寻找创造路": "hint_observe",
                }
                key = hint_map.get(new_hint)
                if key and self.hint_sound_cooldown <= 0:
                    if key == "hint_caution":
                        self.caution_trigger_counter += 1
                        if self.caution_trigger_counter % 50 == 0:
                            self._play_sound_key(key)
                            self.hint_sound_cooldown = 1.0
                    else:
                        self.hint_trigger_counter += 1
                        if self.hint_trigger_counter % 20 == 0:
                            self._play_sound_key(key)
                            self.hint_sound_cooldown = 1.0

            # 地面奔跑动画：更快节奏切换贴图
            if self.horse_img and self.horse_jump_img and self.horse["on_ground"]:
                self.ground_anim_timer += dt
                if self.ground_anim_timer >= 0.18:
                    self.ground_anim_timer -= 0.18
                    self.ground_anim_frame = 1 - self.ground_anim_frame
            else:
                self.ground_anim_timer = 0.0
                self.ground_anim_frame = 0
        else:
            # Even when paused keep fireworks alive at a slower rate.
            self.update_fireworks(dt * 0.3)

        self.canvas.delete("all")
        self.draw_background()
        self.draw_top_lanterns()
        self.draw_fireworks()
        self.draw_obstacles()
        self.draw_horse()
        self.draw_powerups()
        self.draw_air_stars()
        self.draw_hud()

        self.root.after(16, self.tick)

    def start(self) -> None:
        """启动 Tk 事件循环。"""
        self.root.mainloop()


def main() -> None:
    HorseGame().start()


if __name__ == "__main__":
    main()

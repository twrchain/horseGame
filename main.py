
import json
import math
import os
import random
import time

from kivy.app import App
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget


class HorseGameWidget(Widget):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.base_width = 900.0
        self.base_height = 520.0
        self.ground_y = self.base_height - 90.0
        self.gravity = 2200.0
        self.jump_strength = 1100.0
        self.max_air_jumps = 1

        self.obstacles = []
        self.trails = []
        self.fireworks = []
        self.air_stars = []
        self.powerups = []
        self.top_lanterns = []

        self.spawn_timer = 0.0
        self.star_spawn_timer = 0.0
        self.powerup_spawn_timer = 0.0
        self.invincible_timer = 0.0
        self.slow_timer = 0.0
        self.magnet_timer = 0.0
        self.double_score_timer = 0.0
        self.slide_timer = 0.0
        self.slide_cooldown = 0.0
        self.shield = False

        self.current_hint = ""
        self.hint_sound_cooldown = 0.0
        self.jump_sound_counter = 0
        self.jump_prompt_played = False

        self.mode = "endless"
        self.modes = ["endless", "challenge", "timed"]
        self.mode_labels = {"endless": "无尽", "challenge": "挑战", "timed": "计时"}
        self.time_limit = 60.0
        self.game_over_reason = ""

        self.awaiting_start = True
        self.preparing_start = False
        self.countdown_timer = 0.0
        self.paused = False

        self.total_stars = 0
        self.star_combo = 0
        self.star_combo_timer = 0.0
        self.achievements = set()
        self.achievement_text = ""
        self.achievement_timer = 0.0

        self.elapsed = 0.0
        self.distance = 0.0
        self.jumps = 0
        self.air_jumps_used = 0
        self.score = 0
        self.difficulty = 1.0
        self.stage = 0

        self.status_text = "陈思颖: 无尽模式，空格起跳"
        self.last_time = time.time()

        self.scale = 1.0
        self.x_offset = 0.0
        self.y_offset = 0.0

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

        self.volume_levels = [0.0, 0.4, 0.7, 1.0]
        self.volume_index = 2
        self.volume = self.volume_levels[self.volume_index]

        self.sounds = {}
        self.horse_textures = {}

        self.records_path = self._resolve_records_path()
        self.records = self._load_records()

        self._load_assets()
        self.top_lanterns = self._make_top_lanterns()
        self.reset()
        Clock.schedule_interval(self.tick, 1 / 60)

    def _resolve_records_path(self) -> str:
        app = App.get_running_app()
        if app is not None:
            return os.path.join(app.user_data_dir, "horse_records.json")
        return os.path.join(os.path.dirname(__file__), "horse_records.json")

    def _load_records(self) -> dict:
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
            os.makedirs(os.path.dirname(self.records_path), exist_ok=True)
            with open(self.records_path, "w", encoding="utf-8") as handle:
                json.dump(self.records, handle, ensure_ascii=True, indent=2)
        except Exception:
            pass

    def _load_assets(self) -> None:
        base_dir = os.path.join(os.path.dirname(__file__), "image")
        self.horse_textures["main"] = self._load_texture(os.path.join(base_dir, "horse.png"))
        self.horse_textures["jump"] = self._load_texture(os.path.join(base_dir, "horse_jump.png"))
        self.horse_textures["defend"] = self._load_texture(os.path.join(base_dir, "horse_Defend.png"))

        sound_map = {
            "start": "先试一试，空格起跳.MP3",
            "jump": "轻盈跃起！.MP3",
            "double_jump": "连跳加速！.MP3",
            "pause": "暂停.MP3",
            "resume": "继续冲刺.MP3",
            "hit": "撞到障碍了，按 R 继续.MP3",
            "invincible": "星光护体，5秒无敌！.MP3",
            "hint_keep": "保持节奏.MP3",
            "hint_ready": "准备跳！.MP3",
            "hint_caution": "贴近了，小心！.MP3",
            "hint_observe": "观察前方，寻找创造路.MP3",
        }
        for key, filename in sound_map.items():
            path = os.path.join(base_dir, filename)
            if os.path.exists(path):
                self.sounds[key] = SoundLoader.load(path)

    def _load_texture(self, path: str):
        if not os.path.exists(path):
            return None
        try:
            from kivy.core.image import Image as CoreImage

            return CoreImage(path).texture
        except Exception:
            return None

    def _play_sound(self, key: str) -> None:
        sound = self.sounds.get(key)
        if sound and self.volume > 0:
            sound.volume = self.volume
            sound.stop()
            sound.play()

    def _make_top_lanterns(self):
        lanterns = []
        center = self.base_width / 2
        offsets = [180, 270, 360]
        sizes = [random.uniform(34, 54) for _ in offsets]
        ys = [random.uniform(32, 46) for _ in offsets]
        blessings = ["福", "春", "吉祥", "如意", "安康", "平安", "顺意", "招财"]
        for off, size, y in zip(offsets, sizes, ys):
            label = random.choice(blessings)
            lanterns.append({"x": center - off, "y": y, "size": size, "label": label})
            lanterns.append({"x": center + off, "y": y, "size": size, "label": label})
        lanterns.sort(key=lambda l: l["x"])
        return lanterns

    def _make_challenge_pattern(self):
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
        self.horse = {
            "x": 120.0,
            "y": self.ground_y - 70.0,
            "w": 110.0,
            "h": 70.0,
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
        self.slide_timer = 0.0
        self.slide_cooldown = 0.0
        self.shield = False
        self.distance = 0.0
        self.status_text = f"陈思颖: {self.mode_labels[self.mode]}模式，空格起跳"
        self.current_hint = ""
        self.hint_sound_cooldown = 0.0
        self.jump_sound_counter = 0
        self.jump_prompt_played = False
        self.achievements.clear()
        self.achievement_text = ""
        self.achievement_timer = 0.0
        self.difficulty = 1.0
        self.stage = 0
        self.challenge_pattern = self._make_challenge_pattern()
        self.challenge_index = 0
        self.challenge_timer = self.challenge_pattern[0]["delay"] if self.challenge_pattern else 1.0
        self._play_sound("start")

    def start_countdown(self) -> None:
        if self.awaiting_start and not self.preparing_start:
            self.preparing_start = True
            self.countdown_timer = 3.0
            self.status_text = "陈思颖: 准备起跑！"

    def toggle_pause(self) -> None:
        if not self.running or self.awaiting_start or self.preparing_start:
            return
        self.paused = not self.paused
        self.status_text = "陈思颖: 暂停" if self.paused else "陈思颖: 继续冲刺"
        self._play_sound("pause" if self.paused else "resume")

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

    def handle_jump(self) -> None:
        if not self.running or self.paused:
            return
        if self.horse["on_ground"]:
            self._do_jump(self.jump_strength, air_jump=False)
        else:
            if self.air_jumps_used < self.max_air_jumps:
                self._do_jump(self.jump_strength, air_jump=True)

    def handle_slide(self) -> None:
        if not self.horse["on_ground"] or self.slide_cooldown > 0:
            return
        self.slide_timer = 0.45
        self.slide_cooldown = 1.3
        self.status_text = "陈思颖: 滑行闪避！"

    def _do_jump(self, strength: float, air_jump: bool) -> None:
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
                self._play_sound("double_jump")
        else:
            self.status_text = "陈思颖: 轻盈跃起！"
            if not self.jump_prompt_played:
                self._play_sound("jump")
                self.jump_prompt_played = True

    def spawn_obstacle(self, config=None) -> None:
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
                "x": self.base_width + 20.0,
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

    def spawn_firework(self) -> None:
        x = random.uniform(120, self.base_width - 120)
        y = random.uniform(80, self.base_height * 0.4)
        count = random.randint(15, 24)
        particles = []
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(90, 210)
            vx = speed * math.cos(angle)
            vy = speed * math.sin(angle)
            particles.append({"x": x, "y": y, "vx": vx, "vy": vy, "life": random.uniform(0.8, 1.4)})
        color = random.choice(["#ff4d4f", "#ffd166", "#ff7a45", "#ff3859"])
        self.fireworks.append({"particles": particles, "color": color})

    def spawn_star(self) -> None:
        x = self.base_width + 30
        y = random.uniform(120, self.ground_y - 120)
        size = random.uniform(10, 16)
        self.air_stars.append({"x": x, "y": y, "size": size, "speed": random.uniform(220, 320)})

    def spawn_powerup(self) -> None:
        x = self.base_width + 40
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

    def world_speed_multiplier(self) -> float:
        mul = self.difficulty
        if self.invincible_timer > 0:
            mul *= 1.35
        if self.slow_timer > 0:
            mul *= 0.6
        return max(0.4, min(mul, 3.0))

    def update_horse(self, dt: float) -> None:
        self.horse["vy"] += self.gravity * dt
        self.horse["y"] += self.horse["vy"] * dt
        if self.horse["y"] >= self.ground_y - self.horse["h"]:
            self.horse["y"] = self.ground_y - self.horse["h"]
            self.horse["vy"] = 0.0
            self.horse["on_ground"] = True
            self.air_jumps_used = 0
        else:
            self.horse["on_ground"] = False

    def update_obstacles(self, dt: float) -> None:
        speed_mul = self.world_speed_multiplier()
        for obs in self.obstacles:
            obs["x"] -= obs["speed"] * dt * speed_mul
        self.obstacles = [o for o in self.obstacles if o["x"] + o["w"] > -30]

    def update_fireworks(self, dt: float) -> None:
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

    def update_powerups(self, dt: float) -> None:
        speed_mul = self.world_speed_multiplier()
        for p in self.powerups:
            p["x"] -= p["speed"] * dt * speed_mul
        self.powerups = [p for p in self.powerups if p["x"] > -50]

    def check_collisions(self) -> None:
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
                self._play_sound("invincible")
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

    def nearest_hint(self) -> str:
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
        if reason == "hit":
            self.status_text = "陈思颖: 撞到障碍了，点开始继续"
            self._play_sound("hit")
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
    def on_size(self, *args) -> None:
        self._update_scale()

    def _update_scale(self) -> None:
        if self.height <= 0 or self.width <= 0:
            return
        self.scale = min(self.width / self.base_width, self.height / self.base_height)
        self.x_offset = (self.width - self.base_width * self.scale) / 2
        self.y_offset = (self.height - self.base_height * self.scale) / 2

    def _to_screen(self, x, y, w=0, h=0):
        sx = self.x_offset + x * self.scale
        sy = self.y_offset + (self.base_height - y - h) * self.scale
        return sx, sy

    def _color(self, hex_color: str):
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0
        return r, g, b

    def draw(self) -> None:
        self.canvas.clear()
        profile = self.visual_profiles[self.visual_mode]
        band_h = self.base_height / len(profile["sky"])
        with self.canvas:
            for i, color in enumerate(profile["sky"]):
                r, g, b = self._color(color)
                Color(r, g, b)
                sx, sy = self._to_screen(0, i * band_h, self.base_width, band_h)
                Rectangle(pos=(sx, sy), size=(self.base_width * self.scale, band_h * self.scale))

            r, g, b = self._color(profile["ground"])
            Color(r, g, b)
            sx, sy = self._to_screen(0, self.ground_y, self.base_width, self.base_height - self.ground_y)
            Rectangle(pos=(sx, sy), size=(self.base_width * self.scale, (self.base_height - self.ground_y) * self.scale))

            r, g, b = self._color(profile["grid"])
            Color(r, g, b)
            for x in range(0, int(self.base_width + 1), 50):
                x1, y1 = self._to_screen(x, self.ground_y, 0, 0)
                x2, y2 = self._to_screen(x - 40, self.base_height, 0, 0)
                Line(points=[x1, y1, x2, y2], width=1)

            r, g, b = self._color(profile["line"])
            Color(r, g, b)
            x1, y1 = self._to_screen(0, self.ground_y, 0, 0)
            x2, y2 = self._to_screen(self.base_width, self.ground_y, 0, 0)
            Line(points=[x1, y1, x2, y2], width=2)

            r, g, b = self._color(profile["glow"])
            Color(r, g, b)
            for x in range(20, int(self.base_width), 40):
                sx, sy = self._to_screen(x - 2, self.ground_y + 10, 4, 4)
                Ellipse(pos=(sx, sy), size=(4 * self.scale, 4 * self.scale))

            self._draw_lanterns()
            self._draw_fireworks()
            self._draw_obstacles()
            self._draw_horse()
            self._draw_powerups()
            self._draw_stars()

    def _draw_lanterns(self) -> None:
        rope_y = 26
        r, g, b = self._color("#fcbf49")
        Color(r, g, b)
        x1, y1 = self._to_screen(14, rope_y, 0, 0)
        x2, y2 = self._to_screen(self.base_width / 2 - 90, rope_y, 0, 0)
        Line(points=[x1, y1, x2, y2], width=2)
        x3, y3 = self._to_screen(self.base_width / 2 + 90, rope_y, 0, 0)
        x4, y4 = self._to_screen(self.base_width - 14, rope_y, 0, 0)
        Line(points=[x3, y3, x4, y4], width=2)
        for lantern in self.top_lanterns:
            x = lantern["x"]
            y = lantern["y"]
            size = lantern["size"]
            w = size * 1.15
            h = size
            r, g, b = self._color("#e63946")
            Color(r, g, b)
            sx, sy = self._to_screen(x - w / 2, y - h / 2, w, h)
            Ellipse(pos=(sx, sy), size=(w * self.scale, h * self.scale))
            r, g, b = self._color("#ffb703")
            Color(r, g, b)
            sx, sy = self._to_screen(x - 6, y - h / 2 - 6, 12, 12)
            Rectangle(pos=(sx, sy), size=(12 * self.scale, 12 * self.scale))
            r, g, b = self._color("#fcbf49")
            Color(r, g, b)
            x1, y1 = self._to_screen(x, y + h / 2, 0, 0)
            x2, y2 = self._to_screen(x, y + h / 2 + 16, 0, 0)
            Line(points=[x1, y1, x2, y2], width=2)

    def _draw_fireworks(self) -> None:
        for fw in self.fireworks:
            r, g, b = self._color(fw["color"])
            Color(r, g, b)
            for p in fw["particles"]:
                size = max(2, 5 * p["life"])
                sx, sy = self._to_screen(p["x"] - size, p["y"] - size, size * 2, size * 2)
                Ellipse(pos=(sx, sy), size=(size * 2 * self.scale, size * 2 * self.scale))

    def _draw_obstacles(self) -> None:
        for obs in self.obstacles:
            x, y, w, h = obs["x"], obs["y"], obs["w"], obs["h"]
            if obs["theme"] == "fence":
                r, g, b = self._color("#d9d9d9")
                Color(r, g, b)
                sx, sy = self._to_screen(x, y, w, h)
                Rectangle(pos=(sx, sy), size=(w * self.scale, h * self.scale))
                r, g, b = self._color("#8c8c8c")
                Color(r, g, b)
                for bar in range(3):
                    yy = y + h * (bar + 1) / 4
                    x1, y1 = self._to_screen(x, yy, 0, 0)
                    x2, y2 = self._to_screen(x + w, yy, 0, 0)
                    Line(points=[x1, y1, x2, y2], width=2)
            elif obs["theme"] == "data":
                r, g, b = self._color("#3bd8c0")
                Color(r, g, b)
                sx, sy = self._to_screen(x, y, w, h)
                Rectangle(pos=(sx, sy), size=(w * self.scale, h * self.scale))
            elif obs["theme"] == "lantern":
                r, g, b = self._color("#e63946")
                Color(r, g, b)
                sx, sy = self._to_screen(x, y, w, h)
                Ellipse(pos=(sx, sy), size=(w * self.scale, h * self.scale))
                r, g, b = self._color("#ffb703")
                Color(r, g, b)
                sx, sy = self._to_screen(x + w * 0.45, y - 10, w * 0.1, 18)
                Rectangle(pos=(sx, sy), size=(w * 0.1 * self.scale, 18 * self.scale))
            else:
                r, g, b = self._color("#f45b69")
                Color(r, g, b)
                sx, sy = self._to_screen(x, y, w, h)
                Rectangle(pos=(sx, sy), size=(w * self.scale, h * self.scale))

    def _draw_horse(self) -> None:
        x, y, w, h = self.horse["x"], self.horse["y"], self.horse["w"], self.horse["h"]
        texture = None
        if self.invincible_timer > 0 and self.horse_textures.get("defend"):
            texture = self.horse_textures["defend"]
        elif self.horse_textures.get("main") and self.horse_textures.get("jump") and self.horse["on_ground"]:
            texture = self.horse_textures["jump"] if int(time.time() * 6) % 2 else self.horse_textures["main"]
        elif not self.horse["on_ground"] and self.horse_textures.get("jump"):
            texture = self.horse_textures["jump"]
        elif self.horse_textures.get("main"):
            texture = self.horse_textures["main"]

        sx, sy = self._to_screen(x, y, w, h)
        if texture:
            Rectangle(pos=(sx, sy), size=(w * self.scale, h * self.scale), texture=texture)
        else:
            r, g, b = self._color("#f2c14f")
            Color(r, g, b)
            Rectangle(pos=(sx, sy), size=(w * self.scale, h * self.scale))

        if getattr(self, "shield", False):
            r, g, b = self._color("#80ed99")
            Color(r, g, b)
            sx, sy = self._to_screen(x - 6, y - 6, w + 12, h + 12)
            Ellipse(pos=(sx, sy), size=((w + 12) * self.scale, (h + 12) * self.scale))

    def _draw_stars(self) -> None:
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
            scaled = []
            for i in range(0, len(points), 2):
                sx, sy = self._to_screen(points[i], points[i + 1], 0, 0)
                scaled.extend([sx, sy])
            r, g, b = self._color("#fff3b0")
            Color(r, g, b)
            Line(points=scaled, close=True, width=1.5)

    def _draw_powerups(self) -> None:
        style = {
            "slow": ("#7bdff2", "慢"),
            "shield": ("#80ed99", "盾"),
            "magnet": ("#f4acb7", "吸"),
            "double": ("#f9c74f", "倍"),
        }
        for p in self.powerups:
            color, _ = style.get(p["kind"], ("#ffffff", "?"))
            size = p["size"]
            x = p["x"]
            y = p["y"]
            r, g, b = self._color(color)
            Color(r, g, b)
            sx, sy = self._to_screen(x - size, y - size, size * 2, size * 2)
            Ellipse(pos=(sx, sy), size=(size * 2 * self.scale, size * 2 * self.scale))
    def tick(self, dt: float) -> None:
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
                if self.hint_sound_cooldown <= 0:
                    hint_map = {
                        "陈思颖: 保持节奏": "hint_keep",
                        "陈思颖: 准备跳！": "hint_ready",
                        "陈思颖: 贴近了，小心！": "hint_caution",
                        "陈思颖: 观察前方，寻找创造路": "hint_observe",
                    }
                    key = hint_map.get(new_hint)
                    if key:
                        self._play_sound(key)
                        self.hint_sound_cooldown = 1.0

        self.draw()


class HorseGameApp(App):
    def build(self):
        layout = FloatLayout()
        self.game = HorseGameWidget()
        layout.add_widget(self.game)

        self.stats_label = Label(text="", size_hint=(1, None), height=40, pos_hint={"x": 0, "top": 1})
        self.best_label = Label(text="", size_hint=(1, None), height=30, pos_hint={"x": 0, "top": 0.95})
        self.controls_label = Label(text="", size_hint=(1, None), height=30, pos_hint={"x": 0, "top": 0.9})
        self.effects_label = Label(text="", size_hint=(1, None), height=30, pos_hint={"x": 0, "top": 0.85})
        self.status_label = Label(text="", size_hint=(1, None), height=30, pos_hint={"x": 0, "top": 0.8})
        self.achievement_label = Label(text="", size_hint=(1, None), height=30, pos_hint={"x": 0, "top": 0.75})

        for label in [
            self.stats_label,
            self.best_label,
            self.controls_label,
            self.effects_label,
            self.status_label,
            self.achievement_label,
        ]:
            layout.add_widget(label)

        self.start_label = Label(text="准备就绪再出发", size_hint=(1, None), height=40, pos_hint={"x": 0, "center_y": 0.6})
        self.countdown_label = Label(text="", size_hint=(1, None), height=60, pos_hint={"x": 0, "center_y": 0.5})
        self.start_button = Button(text="点击开始", size_hint=(None, None), size=(180, 50), pos_hint={"center_x": 0.5, "center_y": 0.4})
        self.start_button.bind(on_press=lambda *_: self.game.start_countdown())

        self.pause_button = Button(text="暂停", size_hint=(None, None), size=(120, 44), pos_hint={"x": 0.02, "top": 0.98})
        self.pause_button.bind(on_press=lambda *_: self.game.toggle_pause())
        self.mode_button = Button(text="模式", size_hint=(None, None), size=(120, 44), pos_hint={"right": 0.98, "top": 0.98})
        self.mode_button.bind(on_press=lambda *_: self.game.cycle_mode())
        self.jump_button = Button(text="跳", size_hint=(None, None), size=(120, 80), pos_hint={"x": 0.04, "y": 0.04})
        self.jump_button.bind(on_press=lambda *_: self.game.handle_jump())
        self.slide_button = Button(text="滑", size_hint=(None, None), size=(120, 80), pos_hint={"right": 0.96, "y": 0.04})
        self.slide_button.bind(on_press=lambda *_: self.game.handle_slide())

        for widget in [self.start_label, self.countdown_label, self.start_button, self.pause_button, self.mode_button, self.jump_button, self.slide_button]:
            layout.add_widget(widget)

        Window.bind(on_key_down=self._on_key_down)
        Clock.schedule_interval(self._sync_ui, 1 / 30)
        return layout

    def _on_key_down(self, _window, key, scancode, codepoint, modifiers):
        if key == 13:
            if self.game.awaiting_start and not self.game.preparing_start:
                self.game.start_countdown()
                return True
            self.game.toggle_pause()
            return True
        if key == 32:
            self.game.handle_jump()
            return True
        if codepoint in ("s", "S"):
            self.game.handle_slide()
            return True
        if codepoint in ("m", "M"):
            self.game.cycle_mode()
            return True
        if codepoint in ("c", "C"):
            self.game.cycle_visual_mode()
            return True
        if codepoint in ("v", "V"):
            self.game.toggle_volume()
            return True
        if codepoint in ("r", "R"):
            self.game.reset()
            return True
        return False

    def _sync_ui(self, _dt):
        game = self.game
        time_label = f"{game.elapsed:05.2f}s"
        if game.mode == "timed":
            remaining = max(0.0, game.time_limit - game.elapsed)
            time_label = f"{remaining:05.2f}s"
        stats = f"{game.mode_labels[game.mode]}  时间 {time_label}  跃起 {game.jumps}  星星 {game.total_stars}  距离 {game.distance:05.1f}"
        if game.mode == "timed":
            best = f"最佳 计时星星 {game.records['best_timed_score']}  距离 {game.records['best_distance']:.1f}"
        elif game.mode == "challenge":
            best_time = game.records["best_challenge_time"]
            label = f"{best_time:.1f}s" if best_time > 0 else "--"
            best = f"最佳 挑战用时 {label}  星星 {game.records['best_score']}"
        else:
            best = f"最佳 时间 {game.records['best_time']:.1f}s  星星 {game.records['best_score']}  距离 {game.records['best_distance']:.1f}"
        controls = "空格=起跳  S=滑行  M=模式  C=画面  V=音量  Enter=暂停"
        effects = []
        if game.invincible_timer > 0:
            effects.append(f"无敌 {game.invincible_timer:0.1f}s")
        if game.slow_timer > 0:
            effects.append(f"减速 {game.slow_timer:0.1f}s")
        if game.magnet_timer > 0:
            effects.append(f"磁吸 {game.magnet_timer:0.1f}s")
        if game.double_score_timer > 0:
            effects.append(f"翻倍 {game.double_score_timer:0.1f}s")
        if getattr(game, "shield", False):
            effects.append("护盾")

        self.stats_label.text = stats
        self.best_label.text = best
        self.controls_label.text = controls
        self.effects_label.text = " | ".join(effects)
        self.status_label.text = game.status_text
        self.achievement_label.text = game.achievement_text if game.achievement_timer > 0 else ""

        show_start = game.awaiting_start or game.preparing_start
        self.start_label.opacity = 1 if show_start else 0
        self.start_label.disabled = not show_start
        self.start_button.opacity = 1 if game.awaiting_start and not game.preparing_start else 0
        self.start_button.disabled = not (game.awaiting_start and not game.preparing_start)
        self.countdown_label.text = str(int(math.ceil(game.countdown_timer))) if game.preparing_start else ""

        self.pause_button.text = "继续" if game.paused else "暂停"


if __name__ == "__main__":
    HorseGameApp().run()


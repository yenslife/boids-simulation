import pygame
import random
import math
import sys

# --- 常數設定 ---
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
BOID_COUNT = 75
BOID_SIZE = 5
MAX_SPEED = 4
MIN_SPEED = 2

# Boids 演算法參數
VISUAL_RANGE = 75
SEPARATION_DISTANCE = 25

# 規則權重
SEPARATION_FACTOR = 0.05
ALIGNMENT_FACTOR = 0.05
COHESION_FACTOR = 0.0005
EDGE_MARGIN = 50
TURN_FACTOR = 0.2
# 提高避障的權重，讓它成為更優先的行為
OBSTACLE_AVOIDANCE_FACTOR = 0.5

# 捕食者參數
PREDATOR_SIZE = 10
PREDATOR_SPEED = 4.5
PREDATOR_COLOR = (255, 60, 60)
PREDATOR_PEACEFUL_COLOR = (150, 0, 255)
PREDATOR_DETECTION_RANGE = 150
PREDATOR_AVOIDANCE_FACTOR = 0.25
HUNTING_FACTOR = 0.05
PREDATOR_EAT_DISTANCE = 7

# 環境參數
OBSTACLE_COLOR = (120, 120, 120)
OBSTACLE_RADIUS = 20

# UI 介面參數
FONT_SIZE = 20
BUTTON_TEXT_COLOR = (255, 255, 255)
BUTTON_COLOR = (80, 80, 100)
BUTTON_HOVER_COLOR = (120, 120, 150)
INPUT_BOX_COLOR = (50, 50, 60)
INPUT_BOX_ACTIVE_COLOR = (150, 150, 180)


PREDATOR_BUTTON_RECT = pygame.Rect(10, 10, 180, 40)
ADD_BOID_BUTTON_RECT = pygame.Rect(200, 10, 140, 40)
REMOVE_BOID_BUTTON_RECT = pygame.Rect(350, 10, 140, 40)
EAT_MODE_BUTTON_RECT = pygame.Rect(500, 10, 180, 40)
OBSTACLE_MODE_BUTTON_RECT = pygame.Rect(690, 10, 220, 40)
CONTINUOUS_PLACEMENT_BUTTON_RECT = pygame.Rect(920, 10, 200, 40)
TOGGLE_UI_BUTTON_RECT = pygame.Rect(SCREEN_WIDTH - 150, 10, 140, 40)

# 新增輸入框和其確認按鈕
INPUT_BOX_RECT = pygame.Rect(200, 60, 140, 40)
ADD_N_BOIDS_BUTTON_RECT = pygame.Rect(350, 60, 140, 40)


# --- Boid 類別 (獵物) ---
class Boid:
    def __init__(self):
        self.position = pygame.math.Vector2(
            random.uniform(EDGE_MARGIN, SCREEN_WIDTH - EDGE_MARGIN),
            random.uniform(EDGE_MARGIN, SCREEN_HEIGHT - EDGE_MARGIN),
        )
        angle = random.uniform(0, 2 * math.pi)
        self.velocity = pygame.math.Vector2(
            math.cos(angle), math.sin(angle)
        ) * random.uniform(MIN_SPEED, MAX_SPEED)
        self.acceleration = pygame.math.Vector2(0, 0)

    def update(self, boids, predators, obstacles):
        self.acceleration = pygame.math.Vector2(0, 0)

        separation_force = self.separation(boids)
        alignment_force = self.alignment(boids)
        cohesion_force = self.cohesion(boids)
        edge_force = self.avoid_edges()
        predator_force = self.avoid_predators(predators)
        obstacle_force = self.avoid_obstacles(obstacles)

        # 將避障力道的權重設為最高
        self.acceleration += obstacle_force * OBSTACLE_AVOIDANCE_FACTOR
        self.acceleration += separation_force * SEPARATION_FACTOR
        self.acceleration += alignment_force * ALIGNMENT_FACTOR
        self.acceleration += cohesion_force * COHESION_FACTOR
        self.acceleration += edge_force * TURN_FACTOR
        self.acceleration += predator_force * PREDATOR_AVOIDANCE_FACTOR

        self.velocity += self.acceleration

        speed = self.velocity.length()
        if speed > MAX_SPEED:
            self.velocity.scale_to_length(MAX_SPEED)
        elif speed < MIN_SPEED:
            self.velocity.scale_to_length(MIN_SPEED)

        self.position += self.velocity
        return []  # Return empty list for consistency

    def avoid_obstacles(self, obstacles):
        steering = pygame.math.Vector2(0, 0)
        for obs in obstacles:
            dist = self.position.distance_to(obs["center"])
            # 設定一個緩衝區，讓 boid 提早反應
            detection_buffer = 40
            detection_radius = obs["radius"] + detection_buffer

            if dist < detection_radius:
                # 計算一個遠離障礙物中心的力
                diff = self.position - obs["center"]
                # 距離越近，力道越強
                # 當 boid 在緩衝區邊緣時，力道為 0
                # 當 boid 接觸到障礙物時，力道最強
                if dist > 0:
                    strength = (detection_radius - dist) / detection_radius
                    diff.scale_to_length(strength * MAX_SPEED)

                steering += diff
        return steering

    def separation(self, boids):
        steering = pygame.math.Vector2(0, 0)
        count = 0
        for other in boids:
            if self is not other:
                distance = self.position.distance_to(other.position)
                if 0 < distance < SEPARATION_DISTANCE:
                    diff = self.position - other.position
                    diff /= distance
                    steering += diff
                    count += 1
        if count > 0:
            steering /= count
        return steering

    def alignment(self, boids):
        steering = pygame.math.Vector2(0, 0)
        count = 0
        for other in boids:
            if self is not other:
                distance = self.position.distance_to(other.position)
                if 0 < distance < VISUAL_RANGE:
                    steering += other.velocity
                    count += 1
        if count > 0:
            steering /= count
            if steering.length() > 0:
                steering.scale_to_length(MAX_SPEED)
            steering -= self.velocity
        return steering

    def cohesion(self, boids):
        steering = pygame.math.Vector2(0, 0)
        count = 0
        for other in boids:
            if self is not other:
                distance = self.position.distance_to(other.position)
                if 0 < distance < VISUAL_RANGE:
                    steering += other.position
                    count += 1
        if count > 0:
            steering /= count
            steering -= self.position
            if steering.length() > 0:
                steering.scale_to_length(MAX_SPEED)
            steering -= self.velocity
        return steering

    def avoid_edges(self):
        steering = pygame.math.Vector2(0, 0)
        if self.position.x < EDGE_MARGIN:
            steering.x = 1
        elif self.position.x > SCREEN_WIDTH - EDGE_MARGIN:
            steering.x = -1
        if self.position.y < EDGE_MARGIN:
            steering.y = 1
        elif self.position.y > SCREEN_HEIGHT - EDGE_MARGIN:
            steering.y = -1
        return steering

    def avoid_predators(self, predators):
        steering = pygame.math.Vector2(0, 0)
        for predator in predators:
            distance = self.position.distance_to(predator.position)
            if 0 < distance < PREDATOR_DETECTION_RANGE:
                diff = self.position - predator.position
                diff /= distance
                steering += diff
        return steering

    def draw(self, screen):
        angle = self.velocity.angle_to(pygame.math.Vector2(1, 0))
        p1 = self.position + pygame.math.Vector2(BOID_SIZE * 2, 0).rotate(-angle)
        p2 = self.position + pygame.math.Vector2(-BOID_SIZE, BOID_SIZE).rotate(-angle)
        p3 = self.position + pygame.math.Vector2(-BOID_SIZE, -BOID_SIZE).rotate(-angle)
        pygame.draw.polygon(screen, (255, 255, 255), [p1, p2, p3])


# --- Predator 類別 (捕食者) ---
class Predator(Boid):
    def __init__(self):
        super().__init__()
        self.velocity = (
            pygame.math.Vector2(
                random.uniform(-1, 1), random.uniform(-1, 1)
            ).normalize()
            * PREDATOR_SPEED
        )
        self.can_eat = False

    def update(self, boids, predators, obstacles):
        self.acceleration = pygame.math.Vector2(0, 0)

        closest_boid = None
        min_dist = float("inf")
        if boids:
            for boid in boids:
                dist = self.position.distance_to(boid.position)
                if dist < min_dist:
                    min_dist = dist
                    closest_boid = boid

        seek_force = pygame.math.Vector2(0, 0)
        if closest_boid:
            desired_velocity = closest_boid.position - self.position
            if desired_velocity.length() > 0:
                desired_velocity.scale_to_length(PREDATOR_SPEED)
                seek_force = desired_velocity - self.velocity

        edge_force = self.avoid_edges()
        obstacle_force = self.avoid_obstacles(obstacles)

        # 捕食者也需要避障
        self.acceleration += obstacle_force * OBSTACLE_AVOIDANCE_FACTOR * 1.5
        self.acceleration += edge_force * TURN_FACTOR * 2
        self.acceleration += seek_force * HUNTING_FACTOR

        self.velocity += self.acceleration
        if self.velocity.length() > PREDATOR_SPEED:
            self.velocity.scale_to_length(PREDATOR_SPEED)

        self.position += self.velocity

        boids_eaten = []
        if self.can_eat:
            for boid in boids:
                if self.position.distance_to(boid.position) < PREDATOR_EAT_DISTANCE:
                    boids_eaten.append(boid)
        return boids_eaten

    def draw(self, screen):
        current_color = PREDATOR_COLOR if self.can_eat else PREDATOR_PEACEFUL_COLOR
        angle = self.velocity.angle_to(pygame.math.Vector2(1, 0))
        p1 = self.position + pygame.math.Vector2(PREDATOR_SIZE * 2, 0).rotate(-angle)
        p2 = self.position + pygame.math.Vector2(-PREDATOR_SIZE, PREDATOR_SIZE).rotate(
            -angle
        )
        p3 = self.position + pygame.math.Vector2(-PREDATOR_SIZE, -PREDATOR_SIZE).rotate(
            -angle
        )
        pygame.draw.polygon(screen, current_color, [p1, p2, p3])


# --- 主程式 ---
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Boids Simulation - Interactive World Builder")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, FONT_SIZE)

    boids = [Boid() for _ in range(BOID_COUNT)]
    predators = []
    obstacles = []

    predator_active = False
    predator_can_eat = False
    mouse_mode = "add_obstacle"
    ui_visible = True
    continuous_obstacle_placement = False

    # 新增給輸入框的變數
    input_text = "10"
    input_active = False

    def handle_boid_count_change(text_input):
        try:
            num = int(text_input)
            if num > 0:
                for _ in range(num):
                    boids.append(Boid())
            elif num < 0:
                num_to_remove = min(abs(num), len(boids))
                if num_to_remove > 0:
                    for _ in range(num_to_remove):
                        boids.pop(0)  # 移除最舊的
        except ValueError:
            return  # 輸入無效時不執行任何操作

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        clicked_on_ui = False

        # 檢查是否有任何 UI 元素被懸停
        ui_hovered = False
        if ui_visible:
            all_buttons = [
                PREDATOR_BUTTON_RECT,
                ADD_BOID_BUTTON_RECT,
                REMOVE_BOID_BUTTON_RECT,
                EAT_MODE_BUTTON_RECT,
                OBSTACLE_MODE_BUTTON_RECT,
                CONTINUOUS_PLACEMENT_BUTTON_RECT,
                TOGGLE_UI_BUTTON_RECT,
                INPUT_BOX_RECT,
                ADD_N_BOIDS_BUTTON_RECT,
            ]
            for button in all_buttons:
                if button.collidepoint(mouse_pos):
                    ui_hovered = True
                    break

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if input_active:
                    if event.key == pygame.K_RETURN:
                        handle_boid_count_change(input_text)
                        input_text = "10"  # Reset
                    elif event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]
                    elif event.unicode == "-" and len(input_text) == 0:
                        input_text += event.unicode
                    elif event.unicode.isdigit():
                        input_text += event.unicode

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if TOGGLE_UI_BUTTON_RECT.collidepoint(mouse_pos):
                        ui_visible = not ui_visible
                        clicked_on_ui = True

                    if ui_visible:
                        if PREDATOR_BUTTON_RECT.collidepoint(mouse_pos):
                            predator_active = not predator_active
                            clicked_on_ui = True
                        elif ADD_BOID_BUTTON_RECT.collidepoint(mouse_pos):
                            boids.append(Boid())
                            clicked_on_ui = True
                        elif REMOVE_BOID_BUTTON_RECT.collidepoint(mouse_pos):
                            if boids:
                                boids.pop(0)
                            clicked_on_ui = True
                        elif EAT_MODE_BUTTON_RECT.collidepoint(mouse_pos):
                            predator_can_eat = not predator_can_eat
                            clicked_on_ui = True
                        elif OBSTACLE_MODE_BUTTON_RECT.collidepoint(mouse_pos):
                            mouse_mode = (
                                "remove_obstacle"
                                if mouse_mode == "add_obstacle"
                                else "add_obstacle"
                            )
                            clicked_on_ui = True
                        elif CONTINUOUS_PLACEMENT_BUTTON_RECT.collidepoint(mouse_pos):
                            continuous_obstacle_placement = (
                                not continuous_obstacle_placement
                            )
                            clicked_on_ui = True
                        elif INPUT_BOX_RECT.collidepoint(mouse_pos):
                            input_active = True
                            clicked_on_ui = True
                        else:
                            input_active = False

                        if ADD_N_BOIDS_BUTTON_RECT.collidepoint(mouse_pos):
                            handle_boid_count_change(input_text)
                            clicked_on_ui = True

                    if not clicked_on_ui and not continuous_obstacle_placement:
                        if mouse_mode == "add_obstacle":
                            obstacles.append(
                                {
                                    "center": pygame.math.Vector2(mouse_pos),
                                    "radius": OBSTACLE_RADIUS,
                                }
                            )
                        elif mouse_mode == "remove_obstacle":
                            for obs in obstacles[:]:
                                if (
                                    pygame.math.Vector2(mouse_pos).distance_to(
                                        obs["center"]
                                    )
                                    < obs["radius"]
                                ):
                                    obstacles.remove(obs)
                                    break

        # --- 連續滑鼠操作 (新增/移除) ---
        mouse_pressed = pygame.mouse.get_pressed()
        if mouse_pressed[0] and continuous_obstacle_placement and not ui_hovered:
            if mouse_mode == "add_obstacle":
                obstacles.append(
                    {
                        "center": pygame.math.Vector2(mouse_pos),
                        "radius": OBSTACLE_RADIUS,
                    }
                )
            elif mouse_mode == "remove_obstacle":
                for obs in obstacles[:]:
                    if (
                        pygame.math.Vector2(mouse_pos).distance_to(obs["center"])
                        < obs["radius"]
                    ):
                        obstacles.remove(obs)
                        break  # 每幀只移除一個以獲得更好的控制

        if predator_active and not predators:
            predators.append(Predator())
        elif not predator_active and predators:
            predators.clear()
            predator_can_eat = False

        for p in predators:
            p.can_eat = predator_can_eat

        boids_to_remove = set()
        all_entities = boids + predators
        for entity in all_entities:
            eaten = entity.update(boids, predators, obstacles)
            if eaten:
                for boid in eaten:
                    boids_to_remove.add(boid)

        if boids_to_remove:
            boids = [boid for boid in boids if boid not in boids_to_remove]

        screen.fill((10, 20, 40))

        for obs in obstacles:
            pygame.draw.circle(screen, OBSTACLE_COLOR, obs["center"], obs["radius"])

        all_entities = boids + predators
        for entity in all_entities:
            entity.draw(screen)

        # --- 繪製 UI ---
        if ui_visible:
            # ... (所有按鈕的繪製邏輯)
            # 捕食者按鈕
            pred_button_color = (
                BUTTON_HOVER_COLOR
                if PREDATOR_BUTTON_RECT.collidepoint(mouse_pos)
                else BUTTON_COLOR
            )
            pygame.draw.rect(
                screen, pred_button_color, PREDATOR_BUTTON_RECT, border_radius=5
            )
            pred_text_str = "Remove Predator" if predator_active else "Add Predator"
            pred_text = font.render(pred_text_str, True, BUTTON_TEXT_COLOR)
            screen.blit(
                pred_text, pred_text.get_rect(center=PREDATOR_BUTTON_RECT.center)
            )

            # 單一增加 Boid 按鈕
            add_button_color = (
                BUTTON_HOVER_COLOR
                if ADD_BOID_BUTTON_RECT.collidepoint(mouse_pos)
                else BUTTON_COLOR
            )
            pygame.draw.rect(
                screen, add_button_color, ADD_BOID_BUTTON_RECT, border_radius=5
            )
            add_text = font.render("+1 Boid", True, BUTTON_TEXT_COLOR)
            screen.blit(
                add_text, add_text.get_rect(center=ADD_BOID_BUTTON_RECT.center)
            )

            # 單一移除 Boid 按鈕
            remove_button_color = (
                BUTTON_HOVER_COLOR
                if REMOVE_BOID_BUTTON_RECT.collidepoint(mouse_pos)
                else BUTTON_COLOR
            )
            pygame.draw.rect(
                screen, remove_button_color, REMOVE_BOID_BUTTON_RECT, border_radius=5
            )
            remove_text = font.render("-1 Boid", True, BUTTON_TEXT_COLOR)
            screen.blit(
                remove_text,
                remove_text.get_rect(center=REMOVE_BOID_BUTTON_RECT.center),
            )

            # 捕食模式按鈕
            eat_button_color = (
                BUTTON_HOVER_COLOR
                if EAT_MODE_BUTTON_RECT.collidepoint(mouse_pos)
                else BUTTON_COLOR
            )
            pygame.draw.rect(
                screen, eat_button_color, EAT_MODE_BUTTON_RECT, border_radius=5
            )
            eat_text_str = "Disable Eating" if predator_can_eat else "Enable Eating"
            eat_text = font.render(eat_text_str, True, BUTTON_TEXT_COLOR)
            screen.blit(
                eat_text, eat_text.get_rect(center=EAT_MODE_BUTTON_RECT.center)
            )

            # 滑鼠模式按鈕
            obstacle_button_color = (
                BUTTON_HOVER_COLOR
                if OBSTACLE_MODE_BUTTON_RECT.collidepoint(mouse_pos)
                else BUTTON_COLOR
            )
            pygame.draw.rect(
                screen,
                obstacle_button_color,
                OBSTACLE_MODE_BUTTON_RECT,
                border_radius=5,
            )
            obstacle_text_str = (
                "Mouse: Remove Obstacle"
                if mouse_mode == "remove_obstacle"
                else "Mouse: Add Obstacle"
            )
            obstacle_text = font.render(obstacle_text_str, True, BUTTON_TEXT_COLOR)
            screen.blit(
                obstacle_text,
                obstacle_text.get_rect(center=OBSTACLE_MODE_BUTTON_RECT.center),
            )

            # 連續放置模式按鈕
            continuous_button_color = (
                BUTTON_HOVER_COLOR
                if CONTINUOUS_PLACEMENT_BUTTON_RECT.collidepoint(mouse_pos)
                else BUTTON_COLOR
            )
            pygame.draw.rect(
                screen,
                continuous_button_color,
                CONTINUOUS_PLACEMENT_BUTTON_RECT,
                border_radius=5,
            )
            continuous_text_str = (
                "Place: Continuous"
                if continuous_obstacle_placement
                else "Place: Single"
            )
            continuous_text = font.render(
                continuous_text_str, True, BUTTON_TEXT_COLOR
            )
            screen.blit(
                continuous_text,
                continuous_text.get_rect(
                    center=CONTINUOUS_PLACEMENT_BUTTON_RECT.center
                ),
            )

            # 輸入框和相關按鈕
            input_box_color = (
                INPUT_BOX_ACTIVE_COLOR if input_active else INPUT_BOX_COLOR
            )
            pygame.draw.rect(
                screen, input_box_color, INPUT_BOX_RECT, border_radius=5
            )
            input_surface = font.render(input_text, True, BUTTON_TEXT_COLOR)
            screen.blit(
                input_surface, (INPUT_BOX_RECT.x + 10, INPUT_BOX_RECT.y + 10)
            )

            add_n_button_color = (
                BUTTON_HOVER_COLOR
                if ADD_N_BOIDS_BUTTON_RECT.collidepoint(mouse_pos)
                else BUTTON_COLOR
            )
            pygame.draw.rect(
                screen, add_n_button_color, ADD_N_BOIDS_BUTTON_RECT, border_radius=5
            )
            try:
                num = int(input_text)
                button_str = (
                    f"Remove {abs(num)} Boids" if num < 0 else f"Add {num} Boids"
                )
            except ValueError:
                button_str = "Execute"
            add_n_text = font.render(button_str, True, BUTTON_TEXT_COLOR)
            screen.blit(
                add_n_text,
                add_n_text.get_rect(center=ADD_N_BOIDS_BUTTON_RECT.center),
            )

        # 切換 UI 可見性按鈕 (移到最上層繪製)
        toggle_ui_button_color = (
            BUTTON_HOVER_COLOR
            if TOGGLE_UI_BUTTON_RECT.collidepoint(mouse_pos)
            else BUTTON_COLOR
        )
        pygame.draw.rect(
            screen, toggle_ui_button_color, TOGGLE_UI_BUTTON_RECT, border_radius=5
        )
        toggle_ui_text_str = "Hide UI" if ui_visible else "Show UI"
        toggle_ui_text = font.render(toggle_ui_text_str, True, BUTTON_TEXT_COLOR)
        screen.blit(
            toggle_ui_text,
            toggle_ui_text.get_rect(center=TOGGLE_UI_BUTTON_RECT.center),
        )

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()

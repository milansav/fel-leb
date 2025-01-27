import pygame
import random
import sys
import os
import json

pygame.init()

SCREEN_WIDTH, SCREEN_HEIGHT = 640, 480
GRID_SIZE = 10
ROWS, COLS = SCREEN_HEIGHT // GRID_SIZE, SCREEN_WIDTH // GRID_SIZE

WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
BLUE = (0, 0, 255)

FRUIT_TEXTURE = "./resources/Apple.png"

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Snake Game")

CLOCK = pygame.time.Clock()

FONT = pygame.font.Font(None, 36)

UP: tuple[int, int] = (0, -1)
DOWN: tuple[int, int] = (0, 1)
LEFT: tuple[int, int] = (-1, 0)
RIGHT: tuple[int, int] = (1, 0)

HOME_DIR = os.path.expanduser("~")
LEADERBOARDS_FILE_PATH = os.path.join(HOME_DIR, "leaderboards.json")

def load_leaderboards():
    if os.path.exists(LEADERBOARDS_FILE_PATH):
        with open(LEADERBOARDS_FILE_PATH, "r") as file:
            data = json.load(file)
            if isinstance(data, list):
                return data
            else:
                raise ValueError("The JSON file does not contain a list.")
    else:
        return []

loaded_leaderboards = sorted(load_leaderboards(), key=lambda x: x["score"])

def save_leaderboards(username, score):
    new_record = {"username": username, "score": score}
    loaded_leaderboards.append(new_record)
    
    with open(LEADERBOARDS_FILE_PATH, "w") as file:
        json.dump(loaded_leaderboards, file, indent=4)

def find_next_higher_score(current_score) -> dict | None:
    for record in loaded_leaderboards:
        if record["score"] > current_score:
            return record

    return None

class Difficulty:
    Easy = "easy"
    Medium = "medium"
    Hard = "hard"

class Scene:
    def __init__(self, name: str):
        self.name = name

    def render(self):
        raise NotImplementedError()
    
    def handle_events(self):
        pass

    def inject_game(self, game):
        self.game = game

class Game:

  def __init__(self, difficulty: str, screen: pygame.Surface, initial_scene: Scene):
      self.score = 0
      self.running = True
      self.fruits: list[Fruit] = [Fruit()]
      self.screen = screen
      self.snake = Snake(self)
      # self.current_scene = initial_scene
      # self.current_scene.inject_game(self)
      self.scenes: dict[str, Scene] = {}
      self.scenes[initial_scene.name] = initial_scene
      self.current_scene = self.scenes[initial_scene.name]
      self.scenes[initial_scene.name].inject_game(self)

      match difficulty:
          case Difficulty.Easy:
              self.wait_time = 100
          case Difficulty.Medium:
              self.wait_time = 70
          case Difficulty.Hard:
              self.wait_time = 50

      match difficulty:
          case Difficulty.Easy:
              self.min_wait_time = 50
          case Difficulty.Medium:
              self.min_wait_time = 30
          case Difficulty.Hard:
              self.min_wait_time = 15

  def game_over(self):
    self.switch_scene("save_score")

  def update(self):
    self.snake.update()
    for fruit in self.fruits:
      fruit.update(screen)

  def register_scene(self, scene: Scene):
    if self.scenes.get(scene.name) != None:
      raise NameError("A scene with this name is already registered")

    self.scenes[scene.name] = scene
    self.scenes[scene.name].inject_game(game)
    pass

  def switch_scene(self, name: str):
    if self.scenes.get(name) == None:
      raise ValueError("No scene with such name found")

    self.current_scene = self.scenes[name]


class Snake:
    def __init__(self, game: Game):
        self.body = [(10, 10)]
        self.direction = RIGHT
        self.game = game

    def move(self):
        head_x, head_y = self.body[0]
        new_head = (head_x + self.direction[0], head_y + self.direction[1])
        self.body.insert(0, new_head)
        self.body.pop()

    def update(self):
      keys = pygame.key.get_pressed()
      if keys[pygame.K_w] and self.direction != DOWN:
        self.direction = UP
      elif keys[pygame.K_s] and self.direction != UP:
        self.direction = DOWN
      elif keys[pygame.K_a] and self.direction != RIGHT:
        self.direction = LEFT
      elif keys[pygame.K_d] and self.direction != LEFT:
        self.direction = RIGHT

      self.move()

      if self.check_collision():
          self.game.game_over()

      self.check_eat_fruit()

      self.render()


    def render(self):
      for segment in self.body:
          segment_rect = pygame.Rect(segment[0] * GRID_SIZE, segment[1] * GRID_SIZE, GRID_SIZE, GRID_SIZE)
          pygame.draw.rect(screen, WHITE, segment_rect)

    def grow(self):
        tail = self.body[-1]
        self.body.append(tail)

    def check_eat_fruit(self):
      if self.body[0] == self.game.fruits[0].position:
          self.grow()
          self.game.fruits[0].respawn()
          game.score += 1
          wait_time = max(50, self.game.wait_time - 2)
          self.game.wait_time = wait_time

    def check_collision(self):
        head = self.body[0]
        if head in self.body[1:]:
            return True
        if head[0] < 0 or head[1] < 0 or head[0] >= COLS or head[1] >= ROWS:
            return True
        return False

class Fruit:
    def __init__(self):
        self.position = self.random_position()
        self.image = pygame.image.load(FRUIT_TEXTURE)

    def random_position(self):
        return (random.randint(0, COLS - 1), random.randint(0, ROWS - 1))

    def respawn(self):
        self.position = self.random_position()

    def update(self, screen):
        fruit_rect = pygame.Rect(self.position[0] * GRID_SIZE, self.position[1] * GRID_SIZE, GRID_SIZE, GRID_SIZE)
        screen.blit(self.image, fruit_rect)

class MainScene(Scene):
        
    def render(self, _screen: pygame.Surface):
        _screen.fill(BLACK)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.game.running = False

        self.game.update()

        score_text = FONT.render(f"Score: {self.game.score}", True, WHITE)
        _screen.blit(score_text, (10, 10))

        next_higher_score = find_next_higher_score(self.game.score)

        score_to_beat = next_higher_score["score"] if next_higher_score is not None else self.game.score
        player_to_beat = next_higher_score["username"] if next_higher_score is not None else "You"

        highscore_text = FONT.render(f"Score to beat: {score_to_beat} ({player_to_beat})", True, WHITE)
        _screen.blit(highscore_text, (10, 40))

        pygame.display.flip()

        pygame.time.delay(self.game.wait_time)
        CLOCK.tick(30)

class SaveScoreScene(Scene):
    input_box = pygame.Rect(10, 10, 300, 40)
    button_rect = pygame.Rect(10, 60, 100, 40)

    text = ""
    active = False

    def render(self, _screen: pygame.Surface):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.game.running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.input_box.collidepoint(event.pos):
                    self.active = True
                else:
                    self.active = False

                if self.button_rect.collidepoint(event.pos):
                    save_leaderboards(self.text, self.game.score)
                    self.game.running = False

            elif event.type == pygame.KEYDOWN and self.active:
                if event.key == pygame.K_RETURN:
                    save_leaderboards(self.text, self.game.score)
                    self.game.running = False
                    # save_text_to_file(text)
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    self.text += event.unicode

        _screen.fill(WHITE)

        pygame.draw.rect(_screen, BLUE if self.active else GRAY, self.input_box, 2)
        self.text_surface = FONT.render(self.text, True, BLACK)
        _screen.blit(self.text_surface, (self.input_box.x + 5, self.input_box.y + 5))

        # resize limit with text size but limit to screen width with some padding
        self.input_box.w = min(max(300, self.text_surface.get_width() + 10), SCREEN_WIDTH - 10)

        pygame.draw.rect(_screen, GRAY, self.button_rect)
        self.button_text = FONT.render("Save", True, BLACK)
        _screen.blit(self.button_text, (self.button_rect.x + 20, self.button_rect.y + 5))

        pygame.display.flip()

main_scene = MainScene("main_scene")
save_score_scene = SaveScoreScene("save_score")

game = Game(Difficulty.Medium, screen, main_scene)
game.register_scene(save_score_scene)

while game.running:
    game.current_scene.render(game.screen)

pygame.quit()
sys.exit()

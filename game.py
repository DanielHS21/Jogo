import os
os.environ['SDL_VIDEO_CENTERED'] = '1'

import time
import random
import pygame  # necessário para mixer

WIDTH = 1000
HEIGHT = 600

# Inicia o mixer para tocar músicas e sons
pygame.mixer.init()

# Frames
walk_frames = ["player_walk1", "player_walk2"]
walk_frames_flipped = ["player_walk1_flipped", "player_walk2_flipped"]
idle_frame = "player_idle"
idle_frame_flipped = "player_idle_flipped"
attack_frame = "player_attack"
attack_frame_flipped = "player_attack_flipped"

menu_ativo = True
mostrar_instrucoes = False
game_over = False
musica_tocando = False
player_attacking = False

# Player
player = Actor(idle_frame)
player.pos = WIDTH // 2, HEIGHT - 100
player.flip_x = False
player_speed = 5
player.vy = 0

vidas = 3  # Número inicial de vidas
score = 0
max_vidas = 5  # caso queira alterar o número máximo de vidas
heart_image = 'heart'

gravity = 0.5
jump_strength = -10
is_jumping = False
invulneravel = False
invulneravel_duracao = 1.5
invulneravel_fim = 0
ground_y = HEIGHT - 100

current_frame_index = 0
last_frame_time = 0
frame_duration = 0.2

base_platform = Rect((0, HEIGHT - 50), (WIDTH, 50))
ground_y = base_platform.top - player.height / 2

bullets = []
bullet_speed = 8
bullet_cooldown = 0.2
last_shot_time = 0

platforms = []

double_jump_available = False

jump_pressed= False

# Inimigos por horda
enemies = []
current_wave = 1
total_inimigos = 1
def create_enemy():
    enemy = Actor("enemy1_idle")
    enemy.pos = random.randint(50, WIDTH - 50), base_platform.top - enemy.height / 2
    enemy.image_normal = "enemy1_idle"
    enemy.image_flipped = "enemy1_idle_flipped"
    enemy.image = enemy.image_normal
    enemy.direction = 1 if random.choice([True, False]) else -1
    enemy.speed = 2 + current_wave * 0.2
    enemy.vida = 3 + current_wave // 2
    enemy.vy = 0
    enemy.attack_range = 40
    enemy.last_attack = 0
    enemy.attack_cooldown = 1.0
    return enemy

def spawn_wave():
    global enemies
    enemies = [create_enemy() for _ in range(total_inimigos)]

spawn_wave()

def draw():
    global musica_tocando
    screen.blit("background", (0, 0)) 

    if menu_ativo:
        screen.fill((0, 0, 50))
        screen.draw.text("War of the Machines", center=(WIDTH//2, HEIGHT//2 - 100), fontsize=60, color="white")
        screen.draw.text("Pressione ENTER para comecar", center=(WIDTH//2, HEIGHT//2 - 30), fontsize=30, color="gray")
        screen.draw.text("Pressione H para aprender a jogar", center=(WIDTH//2, HEIGHT//2 + 0), fontsize=30, color="gray")
        screen.draw.text("Pressione ESC para sair", center=(WIDTH//2, HEIGHT//2 + 30), fontsize=30, color="gray")

        if not musica_tocando:
            sounds.menu_music.play(-1)
            musica_tocando = True

        if mostrar_instrucoes:
            instrucoes = [
                "COMANDOS:",
                "seta direita ou D: mover para direita",
                "seta esquerda ou A: mover para esquerda",
                "ESPACO: pular (duplo pulo incluso)", 
                "Z ou K: atirar",
                "",
                "OBJETIVO:",
                "Derrote todos os inimigos para avancar para a proxima horda.",
                "Evite ser atacado e sobreviva o maximo que puder!"
            ]
            y = HEIGHT//2 + 100
            for linha in instrucoes:
                screen.draw.text(linha, center=(WIDTH//2, y), fontsize=24, color="white")
                y += 20

        return

    if game_over:
        screen.fill((0,0,0))
        screen.draw.text("GAME OVER", center=(WIDTH//2, HEIGHT//2 - 40), fontsize=60, color="red")
        screen.draw.text("Pressione R para reiniciar", center=(WIDTH//2, HEIGHT//2 + 20), fontsize=30, color="white")
        screen.draw.text("Pressione M para voltar ao menu inicial", center=(WIDTH//2, HEIGHT//2 + 60), fontsize=30, color="white")
        screen.draw.text(f" Total de Pontos: {score}", center=(WIDTH//2, HEIGHT//2 + 100), fontsize=30, color="white")
        return

    screen.blit("background", (0, 0))
    screen.draw.filled_rect(base_platform, (0, 0, 0))

    if not invulneravel or int(time.time() * 10) % 2 == 0:
        player.draw()

    for enemy in enemies:
        enemy.draw()

    for bullet in bullets:
        bullet.draw()

    for i in range(vidas):
        screen.blit(heart_image, (10 + i * 35, 10))

    screen.draw.text(f"Pontos: {score}", topright=(WIDTH - 10, 10), fontsize=30, color="black")
    screen.draw.text(f"Nivel: {current_wave}", center=(WIDTH//2, 10), fontsize=30, color="white", shadow=(1, 1))

    for plat in platforms:
        screen.draw.filled_rect(plat, (100, 100, 100))

def update():
    global current_frame_index, last_frame_time, is_jumping
    global invulneravel, invulneravel_fim, game_over
    global current_wave, total_inimigos, score, double_jump_available, jump_pressed, menu_ativo, mostrar_instrucoes, musica_tocando, player_attacking
    global vidas, max_vidas
    player_old_y = player.y
    player_old_bottom = player.bottom 

    if menu_ativo:
        if keyboard.RETURN:
            menu_ativo = False
            mostrar_instrucoes = False
            sounds.menu_music.stop()
            musica_tocando = False
        elif keyboard.h:
            mostrar_instrucoes = not mostrar_instrucoes
        elif keyboard.escape:
            exit()
        return

    if game_over:
        if keyboard.r:
            reset_game()
        elif keyboard.m:
            game_over = False
            menu_ativo = True
            mostrar_instrucoes = False
            sounds.menu_music.play(-1)
            musica_tocando = True
        return

    moving = False
    if keyboard.left or keyboard.a:
        player.x = max(0, player.x - player_speed)
        moving = True
        player.flip_x = True
    elif keyboard.right or keyboard.d:
        player.x = min(WIDTH, player.x + player_speed)
        moving = True
        player.flip_x = False

    if keyboard.space:
        if not jump_pressed:
            if not is_jumping:
                player.vy = jump_strength
                is_jumping = True
                double_jump_available = True
            elif double_jump_available:
                player.vy = jump_strength
                double_jump_available = False
            jump_pressed = True
    else:
        jump_pressed = False

    player.vy += gravity
    player.y += player.vy

    on_platform = False
    for plat in platforms:
        if player.colliderect(plat) and player.vy >= 0 and player_old_bottom <= plat.top:
            player.bottom = plat.top
            player.vy = 0
            is_jumping = False
            double_jump_available = False
            on_platform = True
            break

    if not on_platform and player.bottom >= ground_y + player.height / 2:
        player.bottom = ground_y + player.height / 2
        player.vy = 0
        is_jumping = False
        double_jump_available = False

    # Atualiza animação do player
    now = time.time()
    if keyboard.z or keyboard.k:
        player_attacking = True
    else:
        player_attacking = False

    if player_attacking:
        player.image = attack_frame_flipped if player.flip_x else attack_frame
    elif moving and not is_jumping:
        if now - last_frame_time > frame_duration:
            last_frame_time = now
            current_frame_index = (current_frame_index + 1) % len(walk_frames)
        player.image = walk_frames_flipped[current_frame_index] if player.flip_x else walk_frames[current_frame_index]
    elif not is_jumping:
        player.image = idle_frame_flipped if player.flip_x else idle_frame

    for bullet in bullets[:]:
        bullet.x += bullet_speed * bullet.direction
        for enemy in enemies[:]:
            if enemy.colliderect(bullet):
                bullets.remove(bullet)
                enemy.vida -= 1
                if enemy.vida <= 0:
                    enemies.remove(enemy)
                    score += 10
                break
        if bullet.x < 0 or bullet.x > WIDTH:
            bullets.remove(bullet)

    if player_attacking:
        shoot()

    for enemy in enemies:
        enemy.x += enemy.speed * enemy.direction
        if enemy.left <= 0 or enemy.right >= WIDTH:
            enemy.direction *= -1
            enemy.image = enemy.image_normal if enemy.direction == 1 else enemy.image_flipped

        if not hasattr(enemy, 'vy'):
            enemy.vy = 0

        enemy.vy += gravity
        enemy.y += enemy.vy

        on_platform = False
        for plat in platforms:
            if enemy.colliderect(plat) and enemy.vy >= 0 and (enemy.bottom - 5) <= plat.top:
                enemy.y = plat.top - enemy.height
                enemy.vy = 0
                on_platform = True
                break

        if not on_platform and enemy.y >= base_platform.top - enemy.height / 2:
            enemy.y = base_platform.top - enemy.height / 2
            enemy.vy = 0

        distance = abs(enemy.x - player.x)
        now = time.time()

        if distance < enemy.attack_range and abs(enemy.y - player.y) < 50:
            if now - enemy.last_attack > enemy.attack_cooldown:
                enemy.image = "enemy1_attack" if enemy.direction == 1 else "enemy1_attack_flipped"
                atacar_jogador()
                enemy.last_attack = now
        else:
            enemy.image = enemy.image_normal if enemy.direction == 1 else enemy.image_flipped

    if not enemies:
        current_wave += 1
        total_inimigos += 1

        # Recupera 1 vida a cada 3 níveis, até o máximo de vidas permitido
        if current_wave % 3 == 0 and vidas < max_vidas:
            vidas += 1

        spawn_wave()
        spawn_platforms()

    if invulneravel and time.time() > invulneravel_fim:
        invulneravel = False

def shoot():
    global last_shot_time
    now = time.time()
    if now - last_shot_time >= bullet_cooldown:
        direction = -1 if player.flip_x else 1
        bullet = Actor("small_bullet1")
        bullet.x = player.x + (25 * direction)
        bullet.y = player.y
        bullet.direction = direction
        bullets.append(bullet)
        last_shot_time = now
        sounds.shot.play()

def atacar_jogador():
    global vidas, invulneravel, invulneravel_fim, game_over
    if not invulneravel:
        vidas -= 1
        invulneravel = True
        invulneravel_fim = time.time() + invulneravel_duracao
        sounds.dano.play()
        if vidas <= 0:
            game_over = True
            sounds.lose.play()

def reset_game():
    global vidas, player, bullets, invulneravel, game_over
    global enemies, current_wave, total_inimigos
    vidas = max_vidas
    player.y = ground_y
    player.x = WIDTH // 2
    player.vy = 0
    bullets.clear()
    invulneravel = False
    game_over = False
    current_wave = 1
    total_inimigos = 1
    spawn_wave()
    spawn_platforms()

def spawn_platforms():
    platforms.clear()
    num_platforms = random.randint(3, 5)

    for _ in range(num_platforms):
        width = random.randint(100, 200)
        height = 20
        x = random.randint(0, WIDTH - width)
        y = random.randint(100, 350)

        platform = Rect((x, y), (width, height))
        platforms.append(platform)

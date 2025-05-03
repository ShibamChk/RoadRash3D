from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random
import time
import keyboard

# Global variables
car_pos = [0, 0, 0]
car_speed = 15
key_state = {b'w': False, b'a': False, b's': False, b'd': False}
lane_centers = [-200, -100, 0, 100, 200]
enemy_cars = [
    {'x': -100, 'y': -200, 'color': (0.8, 0.1, 0.1), 'speed': random.uniform(8.5, 9.2), 'status': 'normal', 'spin_angle': 0, 'spin_timer': 0, 'boost_timer': 0, 'has_damaged_player': False},
    {'x': 0, 'y': -320, 'color': (0.1, 0.8, 0.1), 'speed': random.uniform(8.5, 9.2), 'status': 'normal', 'spin_angle': 0, 'spin_timer': 0, 'boost_timer': 0, 'has_damaged_player': False},
    {'x': 100, 'y': -440, 'color': (0.1, 0.1, 0.8), 'speed': random.uniform(8.5, 9.2), 'status': 'normal', 'spin_angle': 0, 'spin_timer': 0, 'boost_timer': 0, 'has_damaged_player': False}
]

# Add road scroll offset
road_scroll = 0
first_person_view = False
look_angle_x = 0
look_angle_y = 0
lane_width = 100
road_width = lane_width * 5
segment_length = 300
bullets = []
bullet_speed = 50

hit_count = {} # Track hits per enemy car
for i in range(len(enemy_cars)):
    hit_count[i] = 0
heart_timer = 0

life_pickup = None
last_obstacle_hit_time = 0
damage_cooldown_timer = 0


bullet_limit = 10
available_bullets = bullet_limit
game_over = False
player_health = 10
obstacles = []
obstacle_timer = 0

last_bump_time = time.time()
enemy_kill_count = 0
game_won = False

def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(1, 1, 1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_three_lane_road():

    global lane_width , road_width , segment_length
    # Draw road background
    glColor3f(0.1, 0.1, 0.1)
    glBegin(GL_QUADS)
    for i in range(-100, 1000):
        y1 = i * segment_length
        y2 = (i + 1) * segment_length
        glVertex3f(-road_width / 2, y1, 0)
        glVertex3f(road_width / 2, y1, 0)
        glVertex3f(road_width / 2, y2, 0)
        glVertex3f(-road_width / 2, y2, 0)
    glEnd()

    # Simulated lane markers (white rectangles as dashed lines)
    glColor3f(1, 1, 1)
    for x in [-lane_width, lane_width]:  # Divider positions
        for i in range(-100, 1000):
            dash_top = i * segment_length + 100
            dash_bottom = dash_top - 60
            glBegin(GL_QUADS)
            glVertex3f(x - 2, dash_bottom, 1)  # Thin rectangle (lane marks )
            glVertex3f(x + 2, dash_bottom, 1)
            glVertex3f(x + 2, dash_top, 1)
            glVertex3f(x - 2, dash_top, 1)
            glEnd()

    # Side road borders (gray or red)
    glColor3f(0.6, 0.6, 0.6)  # Light gray
    border_width = 10
    for side in [-road_width / 2 - border_width, road_width / 2]:
        glBegin(GL_QUADS)
        for i in range(-100, 1000):
            y1 = i * segment_length
            y2 = (i + 1) * segment_length
            glVertex3f(side, y1, 1)
            glVertex3f(side + border_width, y1, 1)
            glVertex3f(side + border_width, y2, 1)
            glVertex3f(side, y2, 1)
        glEnd()


def draw_starting_line():
    glColor3f(1, 1, 1)
    glBegin(GL_QUADS)
    glVertex3f(-150, 0, 1)
    glVertex3f(150, 0, 1)
    glVertex3f(150, 5, 1)
    glVertex3f(-150, 5, 1)
    glEnd()


def draw_car(x, y, z, color=(0, 0.8, 0), spin_angle=0):
    glPushMatrix()
    glTranslatef(x, y, z + 10)
    glRotatef(-90, 0, 0, 1)
    glRotatef(spin_angle, 0, 0, 1)  # Add spin
    glScalef(0.5, 0.5, 0.5)

    # --- Wheels FIRST ---
    glColor3f(0.1, 0.1, 0.1)
    wheel_positions = [(35, 25, -15), (-35, 25, -15), (35, -25, -15), (-35, -25, -15)]
    for dx, dy, dz in wheel_positions:
        glPushMatrix()
        glTranslatef(dx, dy, dz)
        glRotatef(90, 1, 0, 0)
        glPopMatrix()

    # --- Car Body ---
    glColor3f(*color)
    glPushMatrix()
    glScalef(150, 60, 30)
    glutSolidCube(1)
    glPopMatrix()

    # --- Cabin ---
    glColor3f(color[0]*0.8, color[1]*0.8, color[2]*0.8)
    glPushMatrix()
    glTranslatef(0, 0, 25)
    glScalef(100, 50, 20)
    glutSolidCube(1)
    glPopMatrix()

    # --- Windows (front/back) ---
    glColor3f(0.7, 0.7, 0.7)
    for dx, dy, angle in [(45, 0, 60), (-45, 0, -60)]:
        glPushMatrix()
        glTranslatef(dx, dy, 25)
        glRotatef(angle, 0, 1, 0)
        glScalef(20, 40, 15)
        glutSolidCube(1)
        glPopMatrix()

    # --- Side Windows ---
    for dy in [25, -25]:
        glPushMatrix()
        glTranslatef(0, dy, 25)
        glScalef(50, 5, 15)
        glutSolidCube(1)
        glPopMatrix()

    # --- Roof ---
    glColor3f(color[0]*0.85, color[1]*0.85, color[2]*0.85)
    glPushMatrix()
    glTranslatef(0, 0, 40)
    glScalef(100, 50, 5)
    glutSolidCube(1)
    glPopMatrix()

    glPopMatrix()


def draw_first_person_skeleton():
    if not first_person_view:
        return

    glPushMatrix()
    x, y, z = car_pos

    glTranslatef(x, y + 40, z + 30)  # just ahead of camera

    # Hood
    glColor3f(0.2, 0.2, 0.2)
    glPushMatrix()
    glTranslatef(0, 30, -10)  # position aligned with first-person eye
    glScalef(75, 40, 10)
    glutSolidCube(1)
    glPopMatrix()

    # Top Windshield Bar
    glColor3f(0.1, 0.1, 0.1)
    glPushMatrix()
    glTranslatef(0, 150, 20)
    glScalef(120, 5, 5)
    glutSolidCube(1)
    glPopMatrix()

    # Left Side Frame
    glPushMatrix()
    glTranslatef(-60, 100, 20)
    glScalef(5, 100, 5)
    glutSolidCube(1)
    glPopMatrix()

    # Right Side Frame
    glPushMatrix()
    glTranslatef(60, 100, 20)
    glScalef(5, 100, 5)
    glutSolidCube(1)
    glPopMatrix()

    glPopMatrix()



def draw_shapes():
    glPushMatrix()
    draw_car(car_pos[0], car_pos[1], car_pos[2], (0, 0.8, 0))
    for car in enemy_cars:
        draw_car(car['x'], car['y'], 0, car['color'], spin_angle=car['spin_angle'])

    #  bullets
    glColor3f(1, 1, 0)
    for b in bullets:
        glPushMatrix()
        glTranslatef(b['x'], b['y'], b['z'])
        quad = gluNewQuadric()
        gluSphere(quad, 5, 16, 16)
        glPopMatrix()

    glColor3f(0.8, 0.3, 0.3)
    for obs in obstacles:
        glPushMatrix()
        glTranslatef(obs['x'], obs['y'], 5)
        glScalef(obs['width'], obs['height'], 10)
        glutSolidCube(1)
        glPopMatrix()

    if life_pickup:
        draw_heart_pickup(life_pickup['x'], life_pickup['y'], 10)

    glPopMatrix()

def draw_gun_pointer():
    if not first_person_view:
        return

    glPushMatrix()
    glColor3f(0.9, 0.1, 0.1)  # Red gun pointer

    # Move to the front-center of the player's car
    x, y, z = car_pos
    glTranslatef(x, y + 50, z + 30)  # position ahead of car
    glRotatef(-look_angle_x, 0, 0, 1)
    glRotatef(-90, 1, 0, 0)  # point forward along Y

    #  the gun pointer as a cylinder
    quad = gluNewQuadric()
    gluCylinder(quad, 1.5, 0.5, 40, 10, 10)  # thin cone
    glPopMatrix()



def fire_bullet():
    global available_bullets

    if not first_person_view or available_bullets <= 0:
        return

    #  direction based on look angles
    rad_x = math.radians(look_angle_x)
    rad_y = math.radians(look_angle_y)

    # Bullet starts at the tip of the gun
    gun_x = car_pos[0] + math.sin(rad_x) * 20
    gun_y = car_pos[1] + 40 + math.cos(rad_x) * 20
    gun_z = car_pos[2] + 30 + math.sin(rad_y) * 20

    # Bullet velocity
    vx = math.sin(rad_x) * bullet_speed
    vy = math.cos(rad_x) * bullet_speed
    vz = math.sin(rad_y) * bullet_speed

    bullet = {
        'x': gun_x,
        'y': gun_y,
        'z': gun_z,
        'vx': vx,
        'vy': vy,
        'vz': vz
    }

    bullets.append(bullet)
    available_bullets -= 1



# Check if two cars are overlapping within a bounding box
def is_colliding(car1, car2):
    return abs(car1['x'] - car2['x']) < 60 and abs(car1['y'] - car2['y']) < 80

def draw_heart_pickup(x, y, z):
    glPushMatrix()
    glTranslatef(x, y, z)

    glColor3f(1.0, 0.4, 0.7)  # Pink

    # Left lobe (sphere)
    glPushMatrix()
    glTranslatef(-8, 0, 0)
    gluSphere(gluNewQuadric(), 8, 16, 16)
    glPopMatrix()

    # Right lobe (sphere)
    glPushMatrix()
    glTranslatef(8, 0, 0)
    gluSphere(gluNewQuadric(), 8, 16, 16)
    glPopMatrix()

    # Bottom V (rotated cube)
    glPushMatrix()
    glTranslatef(0, -8, -4)
    glRotatef(45, 0, 0, 1)
    glScalef(8, 8, 8)
    glutSolidCube(1)
    glPopMatrix()

    glPopMatrix()


def chase_player_with_ais():
    for car in enemy_cars:
        if car['status'] != 'normal':
            continue

        # --- Random wandering when far ---
        dx = car_pos[0] - car['x']
        dy = car_pos[1] - car['y']

        if abs(dy) > 300:
            # Wander side to side randomly
            if random.random() < 0.05:
                car['x'] += random.choice([-10, 0, 10])
        else:
            if abs(dx) > 5:
                if dx > 0:
                    direction = 1
                else:
                    direction = -1
                car['x'] += direction * 2  # Smooth tracking

        # Stay on the road
        car['x'] = max(-road_width / 2 + 30, min(road_width / 2 - 30, car['x']))


def handle_collisions():
    global player_health , last_bump_time

    # --- Player vs enemy car collisions ---
    for car in enemy_cars:
        if car['status'] != 'normal':
            continue

        if is_colliding({'x': car_pos[0], 'y': car_pos[1]}, car):
            dx = car['x'] - car_pos[0]

            # Only reduce life if this car hasn't already done so
            if 'has_damaged_player' not in car or car['has_damaged_player'] == False:
                player_health = max(0, player_health - 1)
                last_bump_time = time.time()
                car['has_damaged_player'] = True

            if abs(dx) < 30 and car['y'] > car_pos[1]:
                car['boost_timer'] = 20
            else:
                car['status'] = 'spinning'
                car['spin_timer'] = 30

            # Decrease player life for any collision
            player_health = max(0, player_health - 1)
            last_bump_time = time.time()  # Reset bump timer

    # --- enemy cars colliding with each other ---
    for i in range(len(enemy_cars)):
        for j in range(i + 1, len(enemy_cars)):
            car1 = enemy_cars[i]
            car2 = enemy_cars[j]
            if car1['status'] != 'normal' or car2['status'] != 'normal':
                continue

            if is_colliding(car1, car2):
                if abs(car1['x'] - car2['x']) < 30:
                    if car1['y'] > car2['y']:
                        car2['boost_timer'] = 20
                    else:
                        car1['boost_timer'] = 20
                else:
                    car1['status'] = 'spinning'
                    car1['spin_timer'] = 30
                    car2['status'] = 'spinning'
                    car2['spin_timer'] = 30

    # --- Player vs Obstacle collisions ---
    car_half_width = 30
    car_half_length = 40

    for obs in obstacles[:]:
        obs_half_width = obs['width'] / 2
        obs_half_length = obs['height'] / 2

        if (
                car_pos[0] + car_half_width > obs['x'] - obs_half_width and
                car_pos[0] - car_half_width < obs['x'] + obs_half_width and
                car_pos[1] + car_half_length > obs['y'] - obs_half_length and
                car_pos[1] - car_half_length < obs['y'] + obs_half_length
        ):
            player_health = max(0, player_health - 1)
            obstacles.remove(obs)



def avoid_rear_collisions():
    for car in enemy_cars:
        if car['status'] != 'normal':
            continue

        #  relative position to player
        dx = car['x'] - car_pos[0]
        dy = car['y'] - car_pos[1]

        # Only consider cars behind and approaching player
        if dy < 0 and abs(dx) < 50:  # If within same lane and behind
            distance = abs(dy)
            if not key_state[b'w']:
                closing_speed = car['speed'] - car_speed
            else:
                closing_speed = car['speed']

            #  time until collision
            if closing_speed > 0:
                time_to_collision = distance / closing_speed
            else:
                time_to_collision = float('inf')

            # If collision imminent within 2 seconds
            if time_to_collision < 2.0:
                # Choose avoidance direction (away from center)
                if car_pos[0] > 0:  # Player is right of center
                    avoid_dir = -1  # Move left
                else:  # Player is left of center
                    avoid_dir = 1  # Move right

                # Smooth avoidance maneuver
                car['x'] += avoid_dir * min(5, 50 - abs(dx))

                # Slow down slightly
                car['speed'] = max(5, car['speed'] - 0.5)

def keyboardListener(key, x, y):
    global first_person_view, boost , bullet_limit , available_bullets
    if key in key_state:
        key_state[key] = True
    elif key == b'r':
        reset_game()
    elif key == b'v':
        first_person_view = not first_person_view
    elif key == b' ' and first_person_view and available_bullets > 0:
        fire_bullet()



def reset_game():
    global car_pos, enemy_cars, bullets, hit_count, road_scroll
    global look_angle_x, look_angle_y, game_over, player_health
    global available_bullets, obstacles, life_pickup, heart_timer
    global first_person_view, game_won, damage_cooldown_timer, enemy_kill_count

    # Reset player state
    car_pos = [0, 0, 0]
    road_scroll = 0
    bullets.clear()
    obstacles.clear()
    life_pickup = None
    heart_timer = 0
    first_person_view = False
    look_angle_x = 0
    look_angle_y = 0
    game_over = False
    game_won = False
    player_health = 10
    available_bullets = bullet_limit
    damage_cooldown_timer = 0
    enemy_kill_count = 0

    # Reset enemy cars with random colors (excluding player's color)
    player_color = (0, 0.8, 0)
    color_pool = []
    for i in range(6):
        r = random.uniform(0.0, 1.0)
        g = random.uniform(0.0, 1.0)
        b = random.uniform(0.0, 1.0)
        color_pool.append((r, g, b))

    filtered_colors = []
    for c in color_pool:
        if c != player_color:
            filtered_colors.append(c)
    color_pool = filtered_colors

    random.shuffle(color_pool)

    enemy_cars.clear()
    for i in range(3):
        enemy_cars.append({
            'x': lane_centers[i],
            'y': -80 * (i + 1),
            'color': color_pool[i % len(color_pool)],
            'speed': random.uniform(8.6, 9.0),
            'status': 'normal',
            'spin_angle': 0,
            'spin_timer': 0,
            'boost_timer': 0,
            'has_damaged_player': False
        })

    # Reset hit counters
    hit_count.clear()
    for i in range(len(enemy_cars)):
        hit_count[i] = 0


def specialKeyListener(key, x, y):
    global look_angle_x, look_angle_y

    if key == GLUT_KEY_LEFT:
        look_angle_x -= 5
    elif key == GLUT_KEY_RIGHT:
        look_angle_x += 5
    elif key == GLUT_KEY_UP:
        look_angle_y = min(30, look_angle_y + 2)
    elif key == GLUT_KEY_DOWN:
        look_angle_y = max(-30, look_angle_y - 2)

def mouseListener(button, state, x, y):
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        fire_bullet()


def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, 1.25, 0.1, 2000)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    x, y, z = car_pos

    rad_x = math.radians(look_angle_x)
    rad_y = math.radians(look_angle_y)

    # Shared for both modes
    eye_z = z + 40
    center_x = x + math.sin(rad_x)
    center_y = y + math.cos(rad_x)
    center_z = eye_z + math.sin(rad_y)

    if first_person_view:
        eye_x = x
        eye_y = y + 40
        gluLookAt(eye_x, eye_y, eye_z,
                  center_x, eye_y + math.cos(rad_x), center_z,
                  0, 0, 1)
    else:
        eye_x = x - 300 * math.sin(rad_x)
        eye_y = y - 300 * math.cos(rad_x)
        eye_z = z + 160
        gluLookAt(eye_x, eye_y, eye_z,
                  x, y, z,
                  0, 0, 1)


def idle():
    global road_scroll, car_speed, available_bullets, bullet_limit
    global player_health, game_over, game_won, last_bump_time, enemy_kill_count
    global obstacle_timer, damage_cooldown_timer, heart_timer, life_pickup

    if game_over or game_won:
        return

    if keyboard.is_pressed('w'):
        car_pos[1] += car_speed
    if keyboard.is_pressed('s'):
        car_pos[1] -= car_speed
    if keyboard.is_pressed('a'):
        car_pos[0] = max(car_pos[0] - car_speed, -road_width / 2 + 20)
    if keyboard.is_pressed('d'):
        car_pos[0] = min(car_pos[0] + car_speed, road_width / 2 - 20)
    road_scroll += car_speed * 0.7

    # --- Obstacle Spawning ---
    obstacle_timer += 1
    if obstacle_timer >= 60:
        lane = random.choice(lane_centers)
        distance_ahead = random.randint(400, 800)
        obstacles.append({
            'x': lane,
            'y': car_pos[1] + distance_ahead,
            'width': 60,
            'height': 60
        })
        obstacle_timer = 0

    # --- Heart (Life Pickup) Spawning ---
    heart_timer += 1
    if heart_timer >= random.randint(500, 600) and player_health < 10 and life_pickup is None:
        while True:
            x = random.choice(lane_centers)
            y = car_pos[1] + random.randint(400, 800)

            overlaps = False
            for obs in obstacles:
                if abs(obs['x'] - x) < 60 and abs(obs['y'] - y) < 60:
                    overlaps = True
                    break

            if not overlaps:
                life_pickup = {'x': x, 'y': y, 'width': 60, 'height': 60}
                break
        heart_timer = 0

    # --- Heart Collision Detection ---
    if life_pickup:
        car_half_width = 30
        car_half_length = 40
        heart_half_width = life_pickup['width'] / 2
        heart_half_length = life_pickup['height'] / 2
        if (
            abs(car_pos[0] - life_pickup['x']) < (car_half_width + heart_half_width) and
            abs(car_pos[1] - life_pickup['y']) < (car_half_length + heart_half_length)
        ):
            if player_health < 10:
                player_health += 1
                available_bullets = bullet_limit
            life_pickup = None

    # --- Predictive Obstacle Collisions ---
    for obs in obstacles[:]:
        car_half_width = 30
        car_half_length = 40
        obs_half_width = obs['width'] / 2
        obs_half_length = obs['height'] / 2
        predicted_y = car_pos[1] + (car_speed if key_state[b'w'] else 0)
        if (
            abs(car_pos[0] - obs['x']) < (car_half_width + obs_half_width) and
            abs(predicted_y - obs['y']) < (car_half_length + obs_half_length)
        ):
            if damage_cooldown_timer == 0:
                player_health = max(0, player_health - 1)
                last_bump_time = time.time()
                damage_cooldown_timer = 60
                obstacles.remove(obs)
            break

    # --- enemy car Collision with Player ---
    for car in enemy_cars:
        if car['status'] != 'normal':
            continue
        if 'has_damaged_player' not in car:
            car['has_damaged_player'] = False
        if is_colliding({'x': car_pos[0], 'y': car_pos[1]}, car):
            if not car['has_damaged_player']:
                player_health = max(0, player_health - 1)
                last_bump_time = time.time()
                damage_cooldown_timer = 60
                car['has_damaged_player'] = True
            dx = car['x'] - car_pos[0]
            if abs(dx) < 30 and car['y'] > car_pos[1]:
                car['boost_timer'] = 20
            else:
                car['status'] = 'spinning'
                car['spin_timer'] = 30

    # --- enemy car Behavior ---
    chase_player_with_ais()
    avoid_rear_collisions()

    # --- enemy car Updates ---
    for car in enemy_cars:
        if car['status'] == 'spinning':
            car['spin_angle'] += 15
            car['spin_timer'] -= 1
            if car['spin_timer'] <= 0:
                car['x'] = random.choice(lane_centers)
                car['y'] = car_pos[1] - random.randint(300, 500)
                car['status'] = 'normal'
                car['spin_angle'] = 0
                car['boost_timer'] = 0
                car['has_damaged_player'] = False
            continue

        if car['boost_timer'] > 0:
            car['boost_timer'] -= 1

        distance_behind = car_pos[1] - car['y']
        adjusted_speed = car['speed']

        if distance_behind > 100:
            adjusted_speed = min(car['speed'] + 6, 14)
        if car['boost_timer'] > 0:
            adjusted_speed += 5

        car['y'] += adjusted_speed

        # Respawn enemy car if it goes too far ahead of player
        if car['y'] > car_pos[1] + 800:
            car['x'] = random.choice(lane_centers)
            car['y'] = car_pos[1] - random.randint(400, 700)
            car['has_damaged_player'] = False

    # --- Bullet moving ---
    for bullet in bullets:
        bullet['x'] += bullet['vx']
        bullet['y'] += bullet['vy']
        bullet['z'] += bullet['vz']

    # --- Bullet Collision with enemy cars ---
    to_remove = []
    eliminated = False
    for i, car in enumerate(enemy_cars):
        if car['status'] != 'normal':
            continue
        for bullet in bullets:
            if (
                    abs(bullet['x'] - car['x']) < 30 and
                    abs(bullet['y'] - car['y']) < 40 and
                    abs(bullet['z']) < 30
            ):

                hit_count[i] += 1
                to_remove.append(bullet)
                if hit_count[i] >= 5:
                    car['status'] = 'spinning'
                    car['spin_timer'] = 40
                    hit_count[i] = 0
                    eliminated = True
                    enemy_kill_count += 1

    new_bullets = []
    for b in bullets:
        if b not in to_remove:
            new_bullets.append(b)
    bullets[:] = new_bullets

    if eliminated:
        available_bullets = bullet_limit
        if player_health < 10:
            player_health += 1

    # --- Cooldown Timer Update ---
    if damage_cooldown_timer > 0:
        damage_cooldown_timer -= 1

    # --- Game Win / Over Check ---
    if time.time() - last_bump_time >= 60 or enemy_kill_count >= 5:
        game_won = True
    if player_health <= 0 or available_bullets <= 0:
        game_over = True

    glutPostRedisplay()


def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, 1000, 800)
    setupCamera()

    draw_three_lane_road()
    draw_starting_line()
    draw_shapes()
    draw_first_person_skeleton()
    draw_gun_pointer()



    draw_text(10, 770, f"ROAD RASH-3D")
    draw_text(10, 740, f"Hold W + A/D to steer. Press R to reset.")
    draw_text(10, 710, f"Bullets left: {available_bullets}/10")
    draw_text(10, 690, f"Kills: {enemy_kill_count}")
    draw_text(10, 660, f"Lives: {player_health}/10")
    if game_won:
        draw_text(350, 400, " YOU WON!!!",GLUT_BITMAP_TIMES_ROMAN_24)
        draw_text(360, 370, "Press R to Restart", GLUT_BITMAP_HELVETICA_18)
    elif game_over:
        draw_text(400, 400, "GAME OVER YOU LOST", GLUT_BITMAP_TIMES_ROMAN_24)
        draw_text(360, 370, "Press R to Restart", GLUT_BITMAP_HELVETICA_18)


    glutSwapBuffers()


def init():
    global car_pos, enemy_cars
    # Reset player car position
    car_pos = [0, 0, 0]  # Start at starting line

    # Reset enemy cars positions at starting line with random lane offsets
    lanes = [-200, -100, 0, 100, 200] #defined so that it dosent clash with the player
    random.shuffle(lanes)

    # Define a color pool
    color_pool = [
        (random.random(), random.random(), random.random()),
        (random.random(), random.random(), random.random()),
        (random.random(), random.random(), random.random()),
        (random.random(), random.random(), random.random()),
        (random.random(), random.random(), random.random())
    ]
    random.shuffle(color_pool)

    enemy_cars.clear()
    spacing = 150
    for i in range(3):
        y_offset = -spacing * (i + 1) + random.randint(-30, 30)  # Add slight Y jitter
        enemy_cars.append({
            'x': lanes[i],
            'y': y_offset,
            'color': color_pool[i],
            'speed': round(random.uniform(8.5, 9.0), 2),
            'status': 'normal',
            'spin_angle': 0,
            'spin_timer': 0,
            'boost_timer': 0,
            'has_damaged_player': False
        })
    glClearColor(0.53, 0.81, 0.92, 1.0)  # Sky blue



def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1000, 800)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"Road Rash 3D")
    init()
    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)
    glutMainLoop()

if __name__ == "__main__":
    main()
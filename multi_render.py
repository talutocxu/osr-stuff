import time
import sys
from glob import glob
from os.path import join
import pygame
import pygame.gfxdraw
import random
import argparse
import osr

BLACK = (  0,   0,   0)
GRAY  = (100, 100, 100)
WHITE = (255, 255, 255)

def pick_color():
    return tuple(random.randrange(64, 256) for i in range(3))

def quit():
    print('\n')
    pygame.quit()
    sys.exit(42)

parser = argparse.ArgumentParser(description='osu! replay visualizer')
parser.add_argument('path', help='folder containing replays and mp3')
parser.add_argument('-t', '--tail', help='tail length', type=int, default=100)
parser.add_argument('-r', '--radius', help='circle radius', type=int, default=5)
parser.add_argument('-n', '--no-wipe', help="don't wipe the screen each frame", dest='wipe', action='store_false')
args = parser.parse_args()

pathname = args.path
tail = args.tail
radius = args.radius
wipe = args.wipe

files = glob(join(pathname, '**/*.osr'), recursive=True)
if len(files) == 0:
    sys.exit('no replays to read')

replays = []

for name in files:
    replay = osr.read_file(name)
    # this is hacky but whatever
    replay.color = WHITE if len(files) == 1 else pick_color()
    replays.append(replay)

replays.sort()

n = len(replays)
for r in replays:
    print('%2d. %15s - %d' % (n, r.player, r.score))
    n -= 1
print('read %d replays' % len(replays))

HEIGHT = 768
WIDTH = 1366
KEYSIZE = min((WIDTH-1024)/5, HEIGHT / len(replays))

# Only works with Height of 768 and Width of 1366 if you want different size you will have to work out yourself
# This Change Centers the play on the window just like in Osu client
# Helps with easy overlay for video
X_CHANGE = 273
Y_CHANGE = 89
SCALE = 1.551

pygame.mixer.pre_init(44100)
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('radius=%d tail=%d' % (radius, tail))
pygame.mixer.music.load(*glob(join(pathname, '*.mp3')))
pygame.mixer.music.play()
pygame.mixer.music.set_volume(0.5)
clock = pygame.time.Clock()

UPDATE_FPS = pygame.USEREVENT
pygame.time.set_timer(UPDATE_FPS, 100)

last_pos = 0

screen.fill(BLACK)

while pygame.mixer.music.get_busy():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            quit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                quit()
            elif event.mod & pygame.KMOD_CTRL and event.key == pygame.K_c:
                quit()

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # left mouse button
                radius += 1
            elif event.button == 3: # right mouse button
                radius = max(0, radius - 1)
            elif event.button == 4: # scroll up
                tail += 10
            elif event.button == 5: # scroll down
                tail = max(0, tail - 10)
            if event.button == 2: # middle mouse button
                wipe = not wipe
            pygame.display.set_caption('radius=%d tail=%d' % (radius, tail))

        elif event.type == UPDATE_FPS:
            sys.stderr.write('%5.0f fps\r' % clock.get_fps())

    clock.tick()
    current_pos = pygame.mixer.music.get_pos()
    if wipe:
        screen.fill(BLACK)

    if tail:
        for replay in replays:
            if tail:
                pointlist = []
            last_point = None

            events = replay.replay
            l = len(events)
            hr = replay.has_mod(16)

            for pos in range(max(current_pos-tail, 0), min(l, current_pos)):
                if pos < l:
                    p = events[pos]
                    y = p.y
                    if hr:
                        y = 384 - y
                    x, y = ((p.x + X_CHANGE/SCALE)*SCALE), ((y + Y_CHANGE/SCALE)*SCALE)
                    point = x, y
                    if 0 < x < WIDTH and 0 < y < HEIGHT:
                        if last_point != point:
                            if tail:
                                pointlist.append(point)
                            last_point = point

            if tail and len(pointlist) > 1:
                pygame.draw.lines(screen, replay.color, False, pointlist)

    if radius:
        for replay in replays:
            if current_pos < len(replay):
                p = replay[current_pos]
                y = p.y
                if replay.has_mod(16): # hr
                    y = 384 - y
                x, y = int(((p.x + X_CHANGE/SCALE)*SCALE)), int(((y + Y_CHANGE/SCALE)*SCALE))
                if 0 < x < WIDTH and 0 < y < HEIGHT:
                    pygame.gfxdraw.filled_circle(screen, x, y, radius, replay.color)
                    pygame.gfxdraw.aacircle(screen, x, y, radius, BLACK)

    for i, replay in enumerate(replays):
        p = replay[current_pos]
        y = i*KEYSIZE
        for j, o in enumerate(p.buttons):
            x = WIDTH-KEYSIZE*5+j*KEYSIZE
            screen.fill(replay.color if o else BLACK, (x, y, KEYSIZE, KEYSIZE))

    last_pos = current_pos

    pygame.display.flip()

pygame.quit()

#!/usr/bin/env python3
# Solution to the Mazebot: https://noopschallenge.com/challenges/mazebot

import sys
import copy
import requests
import random
from multiprocessing import cpu_count, Pool
from pprint import pprint

LOGIN = "netromdk"
URL = "https://api.noopschallenge.com"
MAX_TRIES = 10
DEBUG = 1

def build_url(url):
  return URL + url

def get_json(url):
  print("[GET] {}".format(url))
  resp = requests.get(url)
  if not resp:
    print("Failed! code {}".format(resp.status_code))
    print(resp.json())
    return None
  data = resp.json()
  if DEBUG > 1:
    pprint(data)
  elif "message" in data:
    print(data["message"])
  return data

def post_json(url, data):
  print("[POST] {} {}".format(url, data.keys()))
  resp = requests.post(url, json=data)
  if not resp:
    print("Failed! code {}".format(resp.status_code))
    print(resp.json())
    return None
  data = resp.json()
  if DEBUG > 1:
    pprint(data)
  elif "message" in data:
    print(data["message"])
  return data

class Maze:
  def __init__(self, data):
    self.__data = data
    self.__map = data["map"]
    self.__size = len(self.__map[0])
    self.__start = data["startingPosition"]
    self.__pos = self.__start
    self.__prev_pos = self.__pos
    self.__end = data["endingPosition"]
    self.__solution = []
    self.__steps = 0
    self.__solved = False
    self.__next = None

  def __get(self, pos):
    row = pos[0]
    col = pos[1]
    if row < 0 or col < 0 or col >= len(self.__map) or row >= len(self.__map[col]):
      return None
    return self.__map[col][row]

  def __can_go(self, square):
    # It's very important that it's allowed to go back to 'A' since otherwise it can get stuck. For
    # instance, if a blind way is taken then a loop will occur if it cannot go back to 'A' and
    # onwards.
    return square == ' ' or square == 'B' or square == 'A'

  def __current_square(self):
    return self.__get(self.__pos)

  def __advance(self):
    candidates = [([self.__pos[0], self.__pos[1] - 1], 'N'),
                  ([self.__pos[0] + 1, self.__pos[1]], 'E'),
                  ([self.__pos[0], self.__pos[1] + 1], 'S'),
                  ([self.__pos[0] - 1, self.__pos[1]], 'W')]
    (pos, dir) = random.choice(candidates)

    square = self.__get(pos)
    if DEBUG > 2:
      print("try", dir, pos, square)
    if self.__can_go(square):
      self.__prev_pos = self.__pos
      self.__pos = pos
      self.__solution.append(dir)
      self.__steps += 1

  # Remove reduntant steps.
  def __truncate(self):
    s = "".join(self.__solution)
    while True:
      s0 = s.replace("NS", "").replace("SN", "").replace("EW", "").replace("WE", "")
      if s0 == s: break
      s = s0
    self.__solution = s

  def size(self):
    return self.__size

  def solve(self):
    while self.__pos != self.__end:
      if DEBUG > 2:
        square = self.__current_square()
        print("On '{}' ({}), {} steps taken".format(square, self.__pos, self.__steps))
      self.__advance()

    self.__truncate()
    if DEBUG > 2:
      print("Solution:", self.__solution)
    print("Steps:", len(self.__solution))
    self.__solved = True
    return True

  def solved(self):
    return self.__solved

  def steps(self):
    if not self.solved():
      return 0
    return len(self.solution())

  def solution(self):
    return self.__solution

  def next(self):
    return self.__next

  def check(self):
    data = post_json(build_url(self.__data["mazePath"]), {"directions": self.__solution})
    if not data:
      return False
    if "result" in data and data["result"] == "success":
      pprint(data)
      if "nextMaze" in data:
        self.__next = data["nextMaze"]
      return True
    return False

  def clone(self):
    return copy.deepcopy(self)

def random_maze():
  # # Accepted sizes: 10, 20, 30, 40, 60, 100, 120, 150, and 200
  minSize = 10
  maxSize = 100
  data = get_json(build_url("/mazebot/random?minSize={}&maxSize={}".format(minSize, maxSize)))
  if not data:
    return None
  return Maze(data)

def solve_maze(maze):
  if maze.solve():
    return maze
  return None

def async_solve(maze):
  threads = cpu_count()
  mazes = [maze] + [maze.clone() for x in range(threads - 1)]

  pool = Pool(threads)
  results = []
  for m in pool.imap(solve_maze, mazes):
    if m:
      results.append(m)

  if len(results) == 0:
    print("No results! Stopping..")
    return None

  # Pick the shortest solution of the solved mazes.
  maze = min(results, key=lambda m: m.steps())
  if maze.check():
    return maze

  return None

def do_random():
  maze = random_maze()
  if not maze:
    print("Could not get a random maze")
    exit(1)

  print("Trying to solve {}^2 maze..".format(maze.size()))
  async_solve(maze)

def do_race():
  data = post_json(build_url("/mazebot/race/start"), {"login": LOGIN})
  if not data:
    print("Failed to start race!")
    return

  nextMaze = data["nextMaze"]
  stage = 0

  while True:
    data = get_json(build_url(nextMaze))
    if not data:
      print("Failed to get maze: {}".format(nextMaze))
      return

    maze = Maze(data)
    print("Trying to solve {}^2 maze..".format(maze.size()))

    tries = 0
    while tries < MAX_TRIES:
      res = async_solve(maze)
      if not res:
        tries += 1
        print("Could not solve or no next maze, attempt {} of {}".format(tries, MAX_TRIES))
      else:
        stage += 1
        print("Solved stage {}".format(stage))
        nextMaze = res.next()
        break

if __name__ == "__main__":
  if len(sys.argv) != 2:
    print("Usage: {} <mode>".format(sys.argv[0]))
    print("Modes:")
    print("  random   - Gets a random maze and solves it.")
    print("  race     - Starts a race and keeps solving mazes until the race is over.")
    exit(1)

  mode = sys.argv[1].lower()

  if mode == "random":
    do_random()
  elif mode == "race":
    do_race()
  else:
    print("Unknown mode!")
    exit(1)

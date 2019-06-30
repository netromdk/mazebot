#!/usr/bin/env python3
# Solution to the Mazebot: https://noopschallenge.com/challenges/mazebot

import sys
import requests
from pprint import pprint

LOGIN = "netromdk"
URL = "https://api.noopschallenge.com"
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
    self.__reset()

  def __reset(self):
    self.__map = self.__data["map"]
    self.__size = len(self.__map[0])
    self.__start = self.__data["startingPosition"]
    self.__pos = self.__start
    self.__end = self.__data["endingPosition"]
    self.__solved = False
    self.__next = None
    self.__was_here = []  # Positions already visited.
    self.__solution = []

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

  def __can_go_pos(self, pos):
    return self.__can_go(self.__get(pos))

  def __current_square(self):
    return self.__get(self.__pos)

  # Remove redundant steps.
  def __truncate(self):
    s = "".join(self.__solution)
    while True:
      s0 = s.replace("NS", "").replace("SN", "").replace("EW", "").replace("WE", "")
      if s0 == s:
        break
      s = s0
    self.__solution = s

  # Based on https://en.wikipedia.org/wiki/Maze_solving_algorithm#Recursive_algorithm
  def __recursive_solve(self, pos):
    if pos == self.__end:
      return True

    if not self.__can_go_pos(pos) or pos in self.__was_here:
      return False

    self.__was_here.append(pos)

    # If not on the left edge, go west.
    if pos[0] != 0 and self.__recursive_solve([pos[0] - 1, pos[1]]):
      self.__solution.insert(0, "W")
      return True

    # If not on right edge, go east.
    if pos[0] != self.__size - 1 and self.__recursive_solve([pos[0] + 1, pos[1]]):
      self.__solution.insert(0, "E")
      return True

    # If not on top edge, go north.
    if pos[1] != 0 and self.__recursive_solve([pos[0], pos[1] - 1]):
      self.__solution.insert(0, "N")
      return True

    # If not on bottom edge, go south.
    if pos[1] != self.__size - 1 and self.__recursive_solve([pos[0], pos[1] + 1]):
      self.__solution.insert(0, "S")
      return True

    return False

  def size(self):
    return self.__size

  def solve(self):
    self.__solved = self.__recursive_solve(self.__start)
    self.__truncate()

    if DEBUG > 2:
      print("Solution:", self.__solution)
    print("Steps:", len(self.__solution))
    return self.__solved

  def solved(self):
    return self.__solved

  def next(self):
    return self.__next

  def check(self):
    data = post_json(build_url(self.__data["mazePath"]), {"directions": self.__solution})
    if not data:
      return False
    if "result" in data:
      if data["result"] == "success":
        pprint(data)
        if "nextMaze" in data:
          self.__next = data["nextMaze"]
      elif data["result"] == "finished":
        self.__next = None
        if "certificate" in data:
          print("Certificate: {}{}".format(URL, data["certificate"]))
      return True
    return False

def random_maze():
  # # Accepted sizes: 10, 20, 30, 40, 60, 100, 120, 150, and 200
  minSize = 10
  maxSize = 200
  data = get_json(build_url("/mazebot/random?minSize={}&maxSize={}".format(minSize, maxSize)))
  if not data:
    return None
  return Maze(data)

def do_random():
  maze = random_maze()
  if not maze:
    print("Could not get a random maze")
    exit(1)

  print("Trying to solve {}^2 maze..".format(maze.size()))
  if maze.solve():
    maze.check()

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
    if maze.solve() and maze.check():
      stage += 1
      print("Solved stage {}".format(stage))
      nextMaze = maze.next()
      if nextMaze is None:
        break

if __name__ == "__main__":
  sys.setrecursionlimit(4096)

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

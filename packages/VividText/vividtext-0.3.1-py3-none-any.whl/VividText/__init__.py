from time import sleep
import logging
from rich.console import Console

class VividText:

  def __init__(self,
               color="white",
               bold=False,
               dim=False,
               italic=False,
               underline=False,
               reverse=False,
               strike=False,
               sleep=0.05,
               log_saves=False,
               log_path='vividtext.log'):
    self.console = Console()
    self.style_options = {
        "color": color.lower(),
        "bold": bold,
        "dim": dim,
        "italic": italic,
        "underline": underline,
        "reverse": reverse,
        "strike": strike,
    }
    self.sleep = min(sleep, 1)

    self.log_saves = log_saves
    self.log_path = log_path
    self.logger = None
    if self.log_saves:
      self.__setup_logger()

  def toggle_logging(self, enable=None, log_path=None):
      """
      Toggle logging on or off. 
      Optionally provide a new log_path when enabling.

      Args:
          enable (bool or None): Set to True to enable, False to disable, or None to toggle current state.
          log_path (str or None): New log file path to use when enabling logging.
      """
      if enable is None:
          enable = not self.log_saves  # Flip current state

      if enable and not self.log_saves:
          self.log_saves = True
          if log_path:
              self.log_path = log_path
          self.__setup_logger()
          if self.logger:
              self.logger.info("Logging enabled.")

      elif not enable and self.log_saves:
          self.log_saves = False
          if self.logger:
              self.logger.info("Logging disabled.")
              handlers = self.logger.handlers[:]
              for handler in handlers:
                  handler.close()
                  self.logger.removeHandler(handler)
              self.logger = None

  def reset_style(self, color="white", bold=False, dim=False, italic=False, underline=False, reverse=False, strike=False, sleep=0.05):
    self.style_options = {
        "color": color.lower(),
        "bold": bold,
        "dim": dim,
        "italic": italic,
        "underline": underline,
        "reverse": reverse,
        "strike": strike,
    }
    self.sleep = min(sleep, 1)
    if self.logger:
      self.logger.info(f"Change style to: {self.style_options}, Speed: {self.sleep}")

  def __build_style(self):
    style_parts = []

    # Add color (hex, named, or palette all supported)
    if self.style_options["color"]:
      style_parts.append(self.style_options["color"])

    # Add any active style flags
    for attr in ["bold", "dim", "italic", "underline", "reverse", "strike"]:
      if self.style_options[attr]:
        style_parts.append(attr)

    return " ".join(style_parts)

  def __setup_logger(self):
    self.logger = logging.getLogger("VividTextLogger")
    self.logger.setLevel(logging.INFO)
    fh = logging.FileHandler(self.log_path)
    fh.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
    self.logger.addHandler(fh)

  def typewriter(self, msg, end='\n', input=False, slow=False, speed=.7):
    style = self.__build_style()
    if input:
      for i, c in enumerate(msg, 1):
        self.console.print(f"[{style}]{c}[/]", end='', soft_wrap=True)
        sleep(self.sleep)
      if end:
        self.console.print(f"[{style}]{end}[/] ", end='', soft_wrap=True)
        sleep(self.sleep)
    elif slow:
       for i, c in enumerate(msg, 1):
          self.console.print(f"[{style}]{c}[/]",
                             end=end if i == len(msg) else '',
                             soft_wrap=True)
          sleep(speed)
    else:
      for i, c in enumerate(msg, 1):
        self.console.print(f"[{style}]{c}[/]",
                           end=end if i == len(msg) else '',
                           soft_wrap=True)
        sleep(self.sleep)

  def menuTypewriter(self, split, *words):
    if len(words) == 1 and isinstance(words[0], list):
      worded = words[0]
    else:
      worded = list(words)

    formatted = f'{split}'.join(worded)
    self.typewriter(formatted)

  def inputTypewriter(self, msg, end=' >'):
    self.typewriter(msg, end=end, input=True)
    return input()

  def help(self):
    self.console.print(
        "\n[bold underline bright_black]Rich Color Options:[/]\n")

    self.console.print("[bold bright_yellow]Named Colors:[/]")
    self.console.print(
        "red, green, blue, yellow, magenta, cyan, white, and black. You can add bright_[color] for the same colors to make them brighter."
    )

    self.console.print("\n[bold bright_yellow]Hex Colors:[/]")
    self.console.print(
        "[#ff69b4]#ff69b4[/], [#00ffff]#00ffff[/], [#ffaa00]#ffaa00[/], any hex color will work"
    )

    self.console.print("\n[bold bright_yellow]Palette Colors:[/]")
    self.console.print(
        "Use 'color(0)' to 'color(255)'. For example: [color(201)]color(201)[/] is hot pink."
    )

    self.console.print("\n[bold bright_yellow]Attributes:[/]")
    self.console.print("bold, dim, italic, underline, reverse, strike, sleep time")

  def slow_type(self, msg, start_point, end_point=None, speed=.7, end='\n'):
      """
      Print out messages in a slow-typing manner between specified points.

      Args:
          msg (str): The message to print.
          start_point (str|int): Starting character or index for slow printing.
          end_point (str|int|None): Ending character or index for slow printing.
          speed (float): Delay between characters during slow print.
          end (str): End character(s) after the print. Default is newline.
      """
      if not isinstance(msg, str):
          raise TypeError("Message must be a string.")

      # --- Resolve start_index ---
      if isinstance(start_point, str):
          try:
              start_index = msg.index(start_point)
          except ValueError:
              raise ValueError(f"Start character '{start_point}' not found in message.")
      elif isinstance(start_point, int):
          if 0 <= start_point < len(msg):
              start_index = start_point
          else:
              raise IndexError("Start index out of range.")
      else:
          raise TypeError("Start point must be a string or an integer.")

      # --- Resolve end_index ---
      if end_point is None:
          end_index = len(msg)
      elif isinstance(end_point, str):
        try:
            end_index = msg.index(end_point, start_index + 1) + 1  # include end character
        except ValueError:
            end_index = len(msg)  # fallback to end
      elif isinstance(end_point, int):
        if start_index <= end_point < len(msg):
            end_index = end_point + 1  # include the character at the end index
        else:
            raise IndexError("End index out of range or before start.")
      else:
        raise TypeError("End point must be None, a string, or an integer.")
  
      # --- Break message into parts ---
      before = msg[:start_index]
      slow_part = msg[start_index:end_index]
      after = msg[end_index:]

      self.typewriter(before, "")
      if after:
        self.typewriter(slow_part, '', slow=True, speed=speed)
        self.typewriter(after, end=end)
      else:
        self.typewriter(slow_part, slow=True, speed=speed)

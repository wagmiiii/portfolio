/* Portfolio enhancements. No dependencies, no network, nothing required to read the page. */
"use strict";

document.documentElement.classList.remove("no-js");

function copyText(text) {
  if (navigator.clipboard && window.isSecureContext) {
    return navigator.clipboard.writeText(text);
  }
  return Promise.reject(new Error("clipboard unavailable"));
}

function selectText(target) {
  var range = document.createRange();
  range.selectNodeContents(target);
  var selection = window.getSelection();
  selection.removeAllRanges();
  selection.addRange(range);
}

document.querySelectorAll("[data-copy]").forEach(function (button) {
  var target = document.getElementById(button.getAttribute("data-copy"));
  if (!target) {
    button.remove();
    return;
  }
  var label = button.textContent;
  button.addEventListener("click", function () {
    copyText(target.textContent.trim()).then(
      function () {
        button.textContent = "Copied";
        button.dataset.state = "ok";
      },
      function () {
        selectText(target);
        button.textContent = "Selected";
        button.dataset.state = "fail";
      }
    );
    window.setTimeout(function () {
      button.textContent = label;
      delete button.dataset.state;
    }, 2200);
  });
});

/* The name types itself, holds, erases and begins again, so the caret on the heading is doing
   something rather than only blinking. The characters are the ones already in the HTML: they are
   wrapped, never replaced, so the heading keeps its accessible name and its finished width the whole
   time. The heading is also the control that stops the loop: focus it and press Enter, or click it,
   and it finishes the name and stands still. Stopping resolves the name rather than freezing whatever
   fraction the loop had reached. With reduced motion, or without this file, it is simply there. */
(function () {
  var TYPE = 105, ERASE = 46, HOLD = 2600, GAP = 620;
  var mega = document.querySelector(".mega");
  var cursor = mega ? mega.querySelector(".cursor") : null;
  if (!cursor) {
    return;
  }
  var words = Array.prototype.slice.call(mega.children).filter(function (word) {
    return word !== cursor;
  });
  if (words.length !== 2 || window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    return;
  }

  var chars = [];
  var lineOf = [];
  words.forEach(function (word, line) {
    var letters = word.textContent.split("");
    word.textContent = "";
    letters.forEach(function (letter) {
      var span = document.createElement("span");
      span.className = "ch";
      span.textContent = letter;
      word.appendChild(span);
      chars.push(span);
      lineOf.push(line);
    });
  });
  var name = words
    .map(function (word) {
      return word.textContent;
    })
    .join(" ");

  // The instruction lives in the description, not the label, so the hero region keeps the plain name.
  var hint = document.createElement("span");
  hint.className = "vh";
  hint.id = "typing-hint";
  mega.after(hint);
  mega.setAttribute("aria-describedby", hint.id);

  var typed = 0;
  var phase = "type";
  var running = true;
  var timer = null;
  var baselines = [];
  var caretHeight = 0;

  /* The caret stands on the baseline, which is where the in-flow one used to sit. A character box is
     no use for that: the heading's line-height is tighter than its own glyphs, so its box top floats
     above the cap line. An empty inline block has no line box of its own, so its bottom edge is the
     baseline it was placed on. Measured once per layout, not per keystroke. */
  function measure() {
    var box = mega.getBoundingClientRect();
    baselines = words.map(function (word) {
      var probe = document.createElement("span");
      probe.style.cssText = "display:inline-block;width:0;height:0";
      word.appendChild(probe);
      var y = probe.getBoundingClientRect().bottom - box.top;
      probe.remove();
      return y;
    });
    caretHeight = cursor.offsetHeight;
  }

  function place() {
    var index = typed < chars.length ? typed : chars.length - 1;
    var edge = chars[index].getBoundingClientRect();
    // The slot of the character that comes next rather than after the one just typed. That is where a
    // real caret sits, and the name fills the column, so the end of the longest line has no room of
    // its own for a caret.
    var x = (typed < chars.length ? edge.left : edge.right) - mega.getBoundingClientRect().left;
    cursor.style.transform = "translate(" + x + "px," + (baselines[lineOf[index]] - caretHeight) + "px)";
  }

  function show(count) {
    chars.forEach(function (span, i) {
      span.classList.toggle("on", i < count);
    });
    typed = count;
  }

  function step() {
    if (!running) {
      return;
    }
    var wait;
    if (phase === "type") {
      if (typed < chars.length) {
        chars[typed].classList.add("on");
        typed += 1;
        wait = TYPE;
      } else {
        phase = "hold";
        wait = HOLD;
      }
    } else if (phase === "hold") {
      phase = "erase";
      wait = ERASE;
    } else if (typed > 0) {
      typed -= 1;
      chars[typed].classList.remove("on");
      wait = ERASE;
    } else {
      phase = "type";
      wait = GAP;
    }
    place();
    timer = window.setTimeout(step, wait);
  }

  function hintFor(on) {
    return on
      ? "This heading types itself. Press Enter or activate it to stop."
      : "The typing is stopped. Press Enter or activate the heading to run it again.";
  }

  function setRunning(on) {
    running = on;
    if (timer !== null) {
      window.clearTimeout(timer);
      timer = null;
    }
    show(chars.length);
    mega.classList.toggle("mega--paused", !on);
    hint.textContent = hintFor(on);
    if (on) {
      phase = "erase";
      step();
    }
    place();
  }

  mega.classList.add("mega--typing");
  mega.tabIndex = 0;
  hint.textContent = hintFor(true);
  measure();
  window.addEventListener("resize", function () {
    measure();
    place();
  });
  mega.addEventListener("click", function () {
    // Releasing a text selection over the name ends on a click, and selecting the name is a thing
    // people do to a heading.
    if (window.getSelection().toString()) {
      return;
    }
    setRunning(!running);
  });
  mega.addEventListener("keydown", function (event) {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      setRunning(!running);
    }
  });
  step();
})();

/* Below 980px the nav is a drawer. The button owns the open state and CSS reads it off the header,
   so nothing here has to measure the viewport to know whether a drawer even exists. */
(function () {
  var bar = document.querySelector(".bar");
  var toggle = document.querySelector(".menu-toggle");
  var word = toggle ? toggle.querySelector(".menu-word") : null;
  var nav = document.getElementById("site-nav");
  if (!bar || !toggle || !word || !nav) {
    return;
  }

  function setOpen(open) {
    toggle.setAttribute("aria-expanded", open ? "true" : "false");
    word.textContent = open ? "Close" : "Menu";
    if (open) {
      bar.dataset.menu = "open";
    } else {
      delete bar.dataset.menu;
    }
  }

  toggle.addEventListener("click", function () {
    setOpen(bar.dataset.menu !== "open");
  });

  nav.addEventListener("click", function (event) {
    if (event.target.closest("a")) {
      setOpen(false);
    }
  });

  document.addEventListener("click", function (event) {
    if (bar.dataset.menu === "open" && !event.target.closest(".bar")) {
      setOpen(false);
    }
  });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && bar.dataset.menu === "open") {
      setOpen(false);
      toggle.focus();
    }
  });

  // Otherwise a drawer opened on a phone stays logically open after a resize to desktop.
  window.matchMedia("(min-width: 981px)").addEventListener("change", function (event) {
    if (event.matches) {
      setOpen(false);
    }
  });
})();

/* The nav marks the section you are reading, the same way a docs site marks the current page. */
(function () {
  var links = Array.prototype.slice.call(document.querySelectorAll(".nav a[href^='#']"));
  if (!links.length || !("IntersectionObserver" in window)) {
    return;
  }
  var targets = links
    .map(function (link) {
      return document.getElementById(link.getAttribute("href").slice(1));
    })
    .filter(Boolean);

  function mark(id) {
    links.forEach(function (link) {
      if (link.getAttribute("href") === "#" + id) {
        link.setAttribute("aria-current", "true");
      } else {
        link.removeAttribute("aria-current");
      }
    });
  }

  // Ratios survive across callbacks, so a jump between two sections cannot lose the marker to a
  // callback that only carried the section that just left.
  var visible = new Map();
  var observer = new IntersectionObserver(
    function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          visible.set(entry.target.id, entry.intersectionRatio);
        } else {
          visible.delete(entry.target.id);
        }
      });
      var best = null;
      visible.forEach(function (ratio, id) {
        if (best === null || ratio > best.ratio) {
          best = { id: id, ratio: ratio };
        }
      });
      if (best) {
        mark(best.id);
      }
    },
    { rootMargin: "-45% 0px -45% 0px", threshold: [0, 0.25, 0.5] }
  );
  targets.forEach(function (target) {
    observer.observe(target);
  });
})();

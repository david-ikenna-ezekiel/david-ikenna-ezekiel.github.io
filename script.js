(function () {
  if (window.__ARIA_SITE_INITIALIZED__) {
    return;
  }
  window.__ARIA_SITE_INITIALIZED__ = true;

  function onReady(fn) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", fn);
    } else {
      fn();
    }
  }

  function mergeShallow(base, override) {
    var out = {};
    var key;

    for (key in base) {
      if (Object.prototype.hasOwnProperty.call(base, key)) {
        out[key] = base[key];
      }
    }

    if (override && typeof override === "object") {
      for (key in override) {
        if (Object.prototype.hasOwnProperty.call(override, key)) {
          out[key] = override[key];
        }
      }
    }

    return out;
  }

  onReady(function () {
    var defaults = {
      newsletter: {
        audience: "109,050",
        audienceLabel: "entrepreneurs",
        sentence: "I build data products, pipelines... and everything in between. Join The Data Signal - let's build together!",
        customHtml: "I build data products, pipelines&hellip; and everything in between. Join The Data Signal &mdash; let's build together!",
        inputPlaceholder: "Email address",
        buttonLabel: "Subscribe",
      },
      rating: {
        title: "How was this essay?",
        options: [
          { label: "* * *", votes: 1632 },
          { label: "* *", votes: 112 },
          { label: "*", votes: 14 },
        ],
      },
      moreEssays: [
        { slug: "borrowed-confidence", title: "borrowed confidence" },
        { slug: "the-wedge-strategy", title: "the wedge strategy" },
        { slug: "one-metric-that-matters", title: "one metric that matters" },
        { slug: "the-weekly-operating-system", title: "the weekly operating system" },
      ],
    };

    var incoming = window.SITE_CONFIG || {};
    var config = {
      newsletter: mergeShallow(defaults.newsletter, incoming.newsletter),
      rating: mergeShallow(defaults.rating, incoming.rating),
      moreEssays: Array.isArray(incoming.moreEssays) ? incoming.moreEssays : defaults.moreEssays,
    };

    if (!Array.isArray(config.rating.options) || config.rating.options.length === 0) {
      config.rating.options = defaults.rating.options;
    }

    function renderNewsletter() {
      var text = config.newsletter.customHtml;
      if (!text) {
        text =
          'Join <span class="u-text-medium">' +
          config.newsletter.audience +
          "</span> " +
          config.newsletter.audienceLabel +
          " " +
          config.newsletter.sentence;
      }

      var textNodes = document.querySelectorAll(".js-newsletter-text");
      for (var i = 0; i < textNodes.length; i += 1) {
        textNodes[i].innerHTML = text;
      }

      var inputNodes = document.querySelectorAll(".js-newsletter-input");
      for (var j = 0; j < inputNodes.length; j += 1) {
        inputNodes[j].setAttribute("placeholder", config.newsletter.inputPlaceholder);
        inputNodes[j].setAttribute("aria-label", config.newsletter.inputPlaceholder);
      }

      var buttonNodes = document.querySelectorAll(".js-newsletter-button");
      for (var k = 0; k < buttonNodes.length; k += 1) {
        buttonNodes[k].textContent = config.newsletter.buttonLabel;
      }
    }

    function renderMoreEssays() {
      var onEssayPage = window.location.pathname.indexOf("/essays/") !== -1;
      var prefix = onEssayPage ? "" : "essays/";

      var containers = document.querySelectorAll(".js-more-essays");
      for (var i = 0; i < containers.length; i += 1) {
        var html = "";
        for (var m = 0; m < config.moreEssays.length; m += 1) {
          var item = config.moreEssays[m];
          html += '<a class="more-essays-link" href="' + prefix + item.slug + '.html">' + item.title + "</a>";
        }
        containers[i].innerHTML = html;
      }
    }

    function boldQuotedText() {
      var roots = document.querySelectorAll(".page-contain");
      if (!roots.length) {
        return;
      }

      var blockedTags = {
        A: true,
        SCRIPT: true,
        STYLE: true,
        TEXTAREA: true,
        INPUT: true,
        OPTION: true,
        CODE: true,
        PRE: true,
        NOSCRIPT: true,
      };

      function shouldSkipTextNode(node) {
        var parent = node.parentNode;
        if (!parent || parent.nodeType !== 1) {
          return true;
        }

        if (blockedTags[parent.nodeName]) {
          return true;
        }

        if (parent.closest && parent.closest(".quoted-text, a, script, style, textarea, input, option, code, pre, noscript")) {
          return true;
        }

        return false;
      }

      function replaceQuotedSegments(node) {
        var text = node.nodeValue;
        if (!text || (text.indexOf('"') === -1 && text.indexOf("“") === -1)) {
          return;
        }

        var regex = /"[^"\n]+"|“[^”\n]+”/g;
        var match = regex.exec(text);
        if (!match) {
          return;
        }

        var frag = document.createDocumentFragment();
        var cursor = 0;

        while (match) {
          var quoted = match[0];
          var start = match.index;

          if (start > cursor) {
            frag.appendChild(document.createTextNode(text.slice(cursor, start)));
          }

          var strong = document.createElement("strong");
          strong.className = "quoted-text";
          strong.textContent = quoted;
          frag.appendChild(strong);

          cursor = start + quoted.length;
          match = regex.exec(text);
        }

        if (cursor < text.length) {
          frag.appendChild(document.createTextNode(text.slice(cursor)));
        }

        node.parentNode.replaceChild(frag, node);
      }

      for (var r = 0; r < roots.length; r += 1) {
        var walker = document.createTreeWalker(roots[r], NodeFilter.SHOW_TEXT, null);
        var nodes = [];
        var current = walker.nextNode();

        while (current) {
          nodes.push(current);
          current = walker.nextNode();
        }

        for (var i = 0; i < nodes.length; i += 1) {
          if (!shouldSkipTextNode(nodes[i])) {
            replaceQuotedSegments(nodes[i]);
          }
        }
      }
    }

    function makeRatingInteractive(ratingRoot) {
      if (!ratingRoot) {
        return;
      }

      var options = config.rating.options;
      var optionsHtml = "";

      for (var i = 0; i < options.length; i += 1) {
        optionsHtml +=
          '<div class="essay-rating-item">' +
          '<div class="essay-stars">' +
          options[i].label +
          "</div>" +
          '<div class="essay-votes">' +
          options[i].votes +
          "</div>" +
          "</div>";
      }

      ratingRoot.innerHTML =
        '<p class="essay-rating-title">' +
        config.rating.title +
        "</p>" +
        '<div class="essay-rating-grid">' +
        optionsHtml +
        "</div>";

      var ratingItems = Array.prototype.slice.call(ratingRoot.querySelectorAll(".essay-rating-item"));
      var voteEls = [];

      for (var r = 0; r < ratingItems.length; r += 1) {
        voteEls.push(ratingItems[r].querySelector(".essay-votes"));
      }

      var defaultCounts = [];
      for (var d = 0; d < voteEls.length; d += 1) {
        var raw = voteEls[d] && voteEls[d].textContent ? voteEls[d].textContent.replace(/,/g, "").trim() : "0";
        var value = parseInt(raw, 10);
        defaultCounts.push(isNaN(value) ? 0 : value);
      }

      var storageKey = "essay-rating:" + window.location.pathname;
      var state = null;

      try {
        var rawState = window.localStorage.getItem(storageKey);
        if (rawState) {
          state = JSON.parse(rawState);
        }
      } catch (error) {
        state = null;
      }

      if (!state || !Array.isArray(state.counts) || state.counts.length !== ratingItems.length) {
        state = {
          counts: defaultCounts.slice(),
          selected: -1,
        };
      }

      if (typeof state.selected !== "number") {
        state.selected = -1;
      }

      function saveState() {
        try {
          window.localStorage.setItem(storageKey, JSON.stringify(state));
        } catch (error) {
          // Ignore storage errors.
        }
      }

      function renderRating() {
        for (var x = 0; x < ratingItems.length; x += 1) {
          var isActive = state.selected === x;
          ratingItems[x].classList.toggle("is-active", isActive);
          ratingItems[x].setAttribute("aria-pressed", String(isActive));
          if (voteEls[x]) {
            voteEls[x].textContent = String(state.counts[x]);
          }
        }
      }

      function registerVote(index) {
        if (index < 0 || index >= ratingItems.length) {
          return;
        }

        if (state.selected === index) {
          return;
        }

        if (state.selected >= 0 && state.selected < state.counts.length) {
          state.counts[state.selected] = Math.max(0, state.counts[state.selected] - 1);
        }

        state.counts[index] += 1;
        state.selected = index;

        saveState();
        renderRating();
      }

      var _loopIndex = function (index) {
        var item = ratingItems[index];
        item.classList.add("is-interactive");
        item.setAttribute("role", "button");
        item.setAttribute("tabindex", "0");
        item.setAttribute("aria-label", "Rate this essay option " + (index + 1));

        item.addEventListener("click", function () {
          registerVote(index);
        });

        item.addEventListener("keydown", function (event) {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            registerVote(index);
          }
        });
      };

      for (var t = 0; t < ratingItems.length; t += 1) {
        _loopIndex(t);
      }

      renderRating();
    }

    renderNewsletter();
    renderMoreEssays();
    boldQuotedText();

    var ratingRoots = document.querySelectorAll(".js-essay-rating");
    for (var i = 0; i < ratingRoots.length; i += 1) {
      makeRatingInteractive(ratingRoots[i]);
    }
  });
})();

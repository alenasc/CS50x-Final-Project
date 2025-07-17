document.addEventListener("DOMContentLoaded", () => {
  loadWatching();
  loadPopular();
  loadNowPlaying();
  loadWatchlist();
  loadRecommended();
  setupCarousel();
  loadGenres();
  setupFilterPopup();
});

function loadSection(url, containerId) {
  fetch(url)
    .then(res => res.json())
    .then(data => {
      const container = document.getElementById(containerId);
      if (!container) return;

      const titles = Array.isArray(data) ? data : data.titles || [];

      container.innerHTML = "";
      titles.forEach(title => {
        const card = createCard(title);
        container.appendChild(card);
      });
    })
    .catch(err => console.error(`Error loading section ${containerId}:`, err));
}

function scrollRow(rowId, direction) {
  const row = document.getElementById(rowId);
  const scrollAmount = 300;
  row.scrollBy({ left: direction * scrollAmount, behavior: "smooth" });
}


function loadWatching() {
  loadSection("/api/user_titles?status=WATCHING", "watching-container");
}

function loadPopular() {
  loadSection("/api/tmdb/popular", "popular-container");
}

function loadNowPlaying() {
  loadSection("/api/tmdb/now_playing", "nowplaying-container");
}

function loadWatchlist() {
  loadSection("/api/user_titles?status=WATCHLIST", "watchlist-container");
}

function loadRecommended(genres = []) {
  const query = genres.length ? `?genres=${genres.join(",")}` : "";
  loadSection(`/api/tmdb/discover?with_genres=${genres.join(",")}`, "discover-container");
}

function loadGenres() {
  fetch("/api/genres")
    .then(res => res.json())
    .then(data => {
      const genreOptions = document.getElementById("genre-options");
      genreOptions.innerHTML = "";
      const genres = data.movie.concat(data.tv);
      const unique = {};
      genres.forEach(genre => {
        if (!unique[genre.id]) {
          const label = document.createElement("label");
          label.innerHTML = `
            <input type="checkbox" value="${genre.id}"> ${genre.name}
          `;
          genreOptions.appendChild(label);
          unique[genre.id] = true;
        }
      });
    });
}

function setupFilterPopup() {
  const button = document.getElementById("filter-button");
  const popup = document.getElementById("filter-popup");
  const apply = document.getElementById("apply-filters");

  button.addEventListener("click", () => {
    popup.classList.toggle("active");
  });

  apply.addEventListener("click", () => {
    const selected = [...document.querySelectorAll("#genre-options input:checked")].map(input => input.value);
    loadRecommended(selected);
    popup.classList.remove("active");
  });
}

function createCard(title) {
  const card = document.createElement("div");
  const fixedType = title.media_type === "tv" ? "show" : title.media_type;

  card.className = "card";
  card.dataset.titleId = title.tmdb_id;
  card.dataset.mediaType = fixedType;

  const userStatus = title.user_status || "";

  if (title.media_type === "show") {
    title.media_type = "tv";
  }
  
  card.innerHTML = `
    <div class="card-buttons">
      <button type="button" class="rank-btn ${["ABSOLUTE CINEMA", "GREAT", "GOOD", "COULD BE BETTER", "BAD", "WATCHED", "WATCHING"].includes(userStatus) ? "selected" : ""}" data-rank="WATCHED">Watched</button>
      <button type="button" class="rank-btn ${userStatus === "WATCHLIST" ? "selected" : ""}" data-rank="WATCHLIST">Watchlist</button>
      <button type="button" class="rank-btn ${["DIDN'T WATCH", "NOT INTERESTED"].includes(userStatus) ? "selected" : ""}" data-rank="NOT INTERESTED">Not Interested</button>
    </div>
    <a href="/title/${title.tmdb_id}?media_type=${title.media_type}" class="card-link">
      <img src="${title.poster_url}" alt="${title.name}" class="card-poster">
    </a>
  `;

  // Buttons Logic
  card.querySelectorAll(".rank-btn").forEach(button => {
    button.addEventListener("click", () => {
      const tmdbId = card.dataset.titleId;
      const mediaType = card.dataset.mediaType;
      const rank = button.dataset.rank;

      fetch("/rank/quick", {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded"
        },
        body: new URLSearchParams({
          title_id: tmdbId,
          rank: rank,
          media_type: mediaType
        })
      }).then(res => {
        if (!res.ok) {
          throw new Error("Erro ao salvar rank");
        }
        card.querySelectorAll(".rank-btn").forEach(btn => btn.classList.remove("selected"));
        button.classList.add("selected");
      }).catch(err => {
        console.error("Erro no fetch para /rank/quick:", err);
      });
    });
  });

  return card;
}

// Carousel logic 
function setupCarousel() {
  fetch("/api/tmdb/upcoming")
    .then(res => res.json())
    .then(data => {
      const carousel = document.getElementById("carousel");
      const indicators = document.getElementById("carousel-indicators");
      const btnPrev = document.getElementById("carousel-prev");
      const btnNext = document.getElementById("carousel-next");

      carousel.innerHTML = "";
      indicators.innerHTML = "";

      data.forEach((item, index) => {
        const link = document.createElement("a");
        link.href = `/title/${item.tmdb_id}?media_type=${item.media_type}`;
        link.className = "carousel-slide";
        link.style.backgroundImage = `url(${item.backdrop_url || item.poster_url})`;

        link.innerHTML = `
          <div class="carousel-overlay">
            <h1>${item.name}</h1>
          </div>
        `;

        carousel.appendChild(link);

        const dot = document.createElement("div");
        dot.className = index === 0 ? "active" : "";
        dot.addEventListener("click", (e) => {
          e.stopPropagation();
          scrollToSlide(index);
        });
        indicators.appendChild(dot);
      });

      const totalSlides = data.length;
      let currentSlide = 0;

      function scrollToSlide(index) {
        carousel.scrollTo({
          left: index * carousel.offsetWidth,
          behavior: "smooth"
        });
        updateIndicators(index);
        currentSlide = index;
      }

      function updateIndicators(activeIndex) {
        document.querySelectorAll(".carousel-indicators div").forEach((dot, i) => {
          dot.classList.toggle("active", i === activeIndex);
        });
      }

      btnNext.addEventListener("click", () => {
        currentSlide = (currentSlide + 1) % totalSlides;
        scrollToSlide(currentSlide);
      });

      btnPrev.addEventListener("click", () => {
        currentSlide = (currentSlide - 1 + totalSlides) % totalSlides;
        scrollToSlide(currentSlide);
      });

      carousel.addEventListener("scroll", () => {
        const index = Math.round(carousel.scrollLeft / carousel.offsetWidth);
        updateIndicators(index);
        currentSlide = index;
      });

      scrollToSlide(0);
    })
    .catch(error => {
      console.error("Failed to load carousel content:", error);
    });
}



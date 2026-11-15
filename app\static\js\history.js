/* Content history — filter conveniences */
(function () {
  "use strict";

  const filterBar = document.querySelector(".filter-bar");
  if (!filterBar) return;

  const select = filterBar.querySelector('select[name="subject"]');
  if (select) {
    let previous = select.value;
    select.addEventListener("change", () => {
      if (select.value === previous) return;
      previous = select.value;
      filterBar.submit();
    });
  }

  const search = filterBar.querySelector('input[type="search"]');
  if (search) {
    search.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        search.value = "";
        filterBar.submit();
      }
    });
  }
})();

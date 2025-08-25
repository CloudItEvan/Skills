// IntersectionObserver reveal effects with delays
const observer = new IntersectionObserver((entries)=>{
  entries.forEach(e=>{
    if (e.isIntersecting) {
      const delay = e.target.dataset.delay || 0;
      setTimeout(() => e.target.classList.add('visible'), delay);
      observer.unobserve(e.target);
    }
  });
},{ threshold: 0.15 });

document.querySelectorAll('.reveal').forEach(el=>observer.observe(el));



// Lightweight parallax for hero bg
const hero = document.querySelector('.parallax-bg');
if (hero) {
window.addEventListener('scroll', ()=>{
const y = window.scrollY * 0.4; // parallax ratio
hero.style.transform = `translateY(${y}px)`;
});
}

document.addEventListener('DOMContentLoaded', function () {
  const slider = document.getElementById('testimonialSlider');
  const prevBtn = document.getElementById('prevBtn');
  const nextBtn = document.getElementById('nextBtn');
  const dotsContainer = document.getElementById('testimonialDots');

  if (!slider || !prevBtn || !nextBtn || !dotsContainer) return;

  const slides = Array.from(slider.children);
  const dots = Array.from(dotsContainer.children);
  let index = 0;
  let intervalId = null;

  function updateDots() {
    dots.forEach((dot, i) => {
      dot.classList.toggle('bg-gray-700', i === index);
      dot.classList.toggle('bg-gray-300', i !== index);
    });
  }

  function showSlide(i) {
    index = (i + slides.length) % slides.length;
    slider.style.transform = `translateX(-${index * 100}%)`;
    updateDots();
  }

  nextBtn.addEventListener('click', () => showSlide(index + 1));
  prevBtn.addEventListener('click', () => showSlide(index - 1));
  dots.forEach((dot, i) => {
    dot.addEventListener('click', () => showSlide(i));
  });

  function startAuto() {
    stopAuto();
    intervalId = setInterval(() => showSlide(index + 1), 5000);
  }
  function stopAuto() {
    if (intervalId) clearInterval(intervalId);
  }

  const container = slider.parentElement;
  container.addEventListener('mouseenter', stopAuto);
  container.addEventListener('mouseleave', startAuto);

  showSlide(0);
  startAuto();
});

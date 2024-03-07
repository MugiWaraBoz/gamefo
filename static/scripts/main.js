document.addEventListener('DOMContentLoaded', () => {
    intializedSlider();

    // For Register and login
    let registerCover = document.querySelector(".cover_r")
    let loginCover = document.querySelector(".cover_l")
    
    registerCover.addEventListener('click', ()=>{
        
        registerCover.classList.add("opacity_z")
        loginCover.classList.remove("opacity_z")

    });
    
    loginCover.addEventListener('click', ()=>{
        
        loginCover.classList.add("opacity_z")
        registerCover.classList.remove("opacity_z")

    });
    
});

function intializedSlider() {
    if(slides.length > 0){ 
    slides[slideIndex].classList.add("displaySlide");
    intervalID = setInterval(nextSlide, 5000); 
    }
}

// Image slideshow
const slides = document.querySelectorAll(".slides img");
let slideIndex = 0;
let intervalID = null;
function showSlide(index){

    if(index >= slides.length){
        slideIndex = 0;
    } else if(index < 0){
        slideIndex = slides.length -1;
    }

    slides.forEach(slide => {
        slide.classList.remove("displaySlide")
    });
    slides[slideIndex].classList.add("displaySlide");
}
function prevSlide(){
    clearInterval(intervalID);
    slideIndex--;
    showSlide(slideIndex);
}
function nextSlide(){
    slideIndex++;
    showSlide(slideIndex);
}
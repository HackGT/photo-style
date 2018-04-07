const video = document.querySelector(".player");
const canvas = document.querySelector(".photo");
const ctx = canvas.getContext("2d");
const strip = document.querySelector(".strip");
const snap = document.querySelector(".snap");
const shutter = document.querySelector(".take-photo");
const buttons = document.querySelectorAll("a");
const effectControls = document.querySelectorAll(".controls");
const colorizeControls = document.querySelectorAll('input[name="colorize"]');
var currentData = ''

const getVideo = () => {
    navigator.mediaDevices
        .getUserMedia({
            video: true,
            audio: false
        })
        .then(localMediaStream => {
            video.src = window.URL.createObjectURL(localMediaStream);
            video.play();
        })
        .catch(err => {
            console.error(`error`, err);
        });
};
let activeEffect = null;
const handleControls = e => {
    e.preventDefault();
    const control = e.target.dataset.control;
    if (control === "takePhoto") {
        takePhoto();
        return;
    } else if (control === activeEffect) {
        activeEffect = null;
        buttons.forEach(button => button.classList.remove("active"));
        effectControls.forEach(controls => controls.classList.remove("active"));
    } else {
        buttons.forEach(button => button.classList.remove("active"));
        e.target.classList.add("active");
        activeEffect = control;
        effectControls.forEach(controls => controls.classList.remove("active"));
        const activeControls = document.querySelector(
            `[data-effect=${activeEffect}]`
        );
        activeControls ? activeControls.classList.add("active") : null;
    }
};
const paintToCanvas = () => {
    const width = video.videoWidth;
    const height = video.videoHeight;
    canvas.width = width;
    canvas.height = height;

    return setInterval(() => {
        ctx.drawImage(video, 0, 0, width, height);
        let pixels = ctx.getImageData(0, 0, width, height);
        if (activeEffect === "colorize") {
            ctx.globalAlpha = 1;
            colorize(pixels);
        } else if (activeEffect === "spectrascope") {
            ctx.globalAlpha = 0.3;
            spectrascope(pixels);
        } else if (activeEffect === "chromakey") {
            ctx.globalAlpha = 1;
            chromakey(pixels);
        }
        ctx.putImageData(pixels, 0, 0);
    }, 16);
};

const takePhoto = () => {
    $("#countdown").countdown360({
        radius: 60.5,
        seconds: 3,
        strokeWidth: 15,
        fillStyle: '#0276FD',
        strokeStyle: '#003F87',
        fontSize: 50,
        fontColor: '#FFFFFF',
        autostart: false,
        onComplete: function () {
            snap.currentTime = 0;
            snap.play();

            const data = canvas.toDataURL("image/jpeg");
            currentData = data;
            const link = document.createElement("a");
            link.href = data;
            link.setAttribute("download", "photo");
            link.classList.add("photo");
            link.innerHTML = `<img src="${data}" alt="photo" />`;
            strip.insertBefore(link, strip.firstChild);
        }
    }).start()

};

const colorize = pixels => {
    for (let i = 0; i < pixels.data.length; i += 4) {
        pixels.data[i + 0] = pixels.data[i + 0] + colorizeColor[0] * 50;
        pixels.data[i + 1] = pixels.data[i + 1] + colorizeColor[1] * 50;
        pixels.data[i + 2] = pixels.data[i + 2] + colorizeColor[2] * 50;
    }
    return pixels;
};
const handleColorize = e => {
    colorizeColor = e.target.dataset.factor
        .split(", ")
        .map(val => parseFloat(val));
};

const spectrascope = pixels => {
    for (let i = 0; i < pixels.data.length; i += 4) {
        pixels.data[i - 150] = pixels.data[i + 0];
        pixels.data[i + 100] = pixels.data[i + 1];
        pixels.data[i - 100] = pixels.data[i + 2];
    }
    return pixels;
};

const chromakey = pixels => {
    const levels = {};

    document.querySelectorAll(".rgb input").forEach(input => {
        levels[input.name] = input.value;
    });

    for (i = 0; i < pixels.data.length; i = i + 4) {
        red = pixels.data[i + 0];
        green = pixels.data[i + 1];
        blue = pixels.data[i + 2];
        alpha = pixels.data[i + 3];

        if (
            red >= levels.rmin &&
            green >= levels.gmin &&
            blue >= levels.bmin &&
            red <= levels.rmax &&
            green <= levels.gmax &&
            blue <= levels.bmax
        ) {
            pixels.data[i + 3] = 0;
        }
    }

    return pixels;
};

$(document).ready(function () {
    $('#takephoto').click(function (e) {
        e.preventDefault()
        if ($('#phone').val() && $('#filter').val() !== 'Select Filter Style') {
            $('#myModal').modal()
            getVideo();
        } else {
            iziToast.error({
                title: 'Error',
                message: 'Fill out all fields'
            });
        }
    })

    $('#sendphoto').click(function (e) {
        e.preventDefault()
        if (currentData) {
            $.post("http://128.61.105.52/convert_encoded", {
                image_url: currentData,
                style: $('#filter').val()
            }, function (data, status) {
                console.log(data, status)
                if (status == 200) {
                    iziToast.info({
                        title: 'FYI',
                        message: 'Photo processed!'
                    });
                    var url = data.url;
                    $.post("http://128.61.105.52/send-mms", {
                        phone: $('#phone').val(),
                        url: url
                    }, function (data, status) {
                        console.log(data, status)
                        if (status == 200) {
                            iziToast.success({
                                title: 'FYI',
                                message: 'Photo messaged!'
                            });
                        } else {
                            iziToast.error({
                                title: 'Error',
                                message: 'Something went wrong'
                            });
                        }
                    })
                } else {
                    iziToast.error({
                        title: 'Error',
                        message: 'Something went wrong'
                    });
                }
            }).fail(function () {
                iziToast.error({
                    title: 'Error',
                    message: 'Something went wrong'
                });
            });
        } else {
            iziToast.error({
                title: 'Error',
                message: 'No photo taken'
            });
        }
    })
})

let colorizeColor = [1, -1, -1];
colorizeControls.forEach(input =>
    input.addEventListener("change", handleColorize)
);

buttons.forEach(button => button.addEventListener("click", handleControls));
video.addEventListener("canplay", paintToCanvas);

// TODO: video as fallback as dslr
const video = document.querySelector("#video-player");
const canvas = document.querySelector("#booth-photo");
const previewCanvas = document.querySelector('#preview-photo');
const ctx = canvas.getContext("2d");
const previewCtx = previewCanvas.getContext("2d");
const activeCanvas = document.querySelector("#active-layer");
const activeCtx = activeCanvas.getContext("2d");
const hoverCanvas = document.querySelector("#hover-layer");
const hoverCtx = hoverCanvas.getContext("2d");

const snap = document.querySelector(".snap");
const backendUri = "http://64.62.141.7:8080/";
const requestFiltersUri = backendUri + "convert_encoded";
const sendMessageUri = backendUri + "send_mms";
const takePhotoUri = '/capture';
var currentFrame = '';
const OUTLINE_OFFSET = 100;
var applyMask = () => console.error("Apply mask called before binding");
var applyActiveOutline = () => console.error("Apply active outline called before binding");
var applyHoverOutline = () => console.error("Apply hover outline called before binding");

// Mask id of people/background
var hoverId = -1; // - 1 is none
var activeId = -1;
var activeFilters = { // store of applied filters per key/entity
    0: '',
    1: '',
    2: '',
    3: '',
};

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

const takePhoto = () => {
    filterData = '';
    currentFrame = '';
    $("#take-photo").attr("disabled", true);
    $('#countdown-wrap').show();
    $("#countdown").countdown360({
        radius: 60.5,
        seconds: 1,
        strokeWidth: 15,
        fillStyle: '#FFF',
        strokeStyle: '#000',
        fontSize: 50,
        fontColor: '#000',
        autostart: false,
        onComplete: function () {
            snap.currentTime = 0;
            snap.play();
            video.pause();
            // Alternatively, call '/capture' here (if we want countdown)
            // await response and move on to preview
            // assume we have image in next stage
            // if we can't get preview, just send to backend, no preview stage
            
            $('#countdown-wrap').hide();
            $('#take-check').show();
            $('#take-photo').hide();
            
            $.ajax({
                type: "POST",
                url: takePhotoUri,
                timeout: 10000,
                success: function (data, status) {
                    console.log(data, status);
                    if (status == "success") {
                        const { image } = data;
                        const img = new Image();
                        const url = `data:image/jpeg;base64,${image}`;
                        img.onload = function(){
                            previewCanvas.width = img.width;
                            previewCanvas.height = img.height;
                            previewCtx.drawImage(img, 0, 0);
                        };
                        img.src = url;
			$('#video-player').hide();
            		$('#preview-photo').show();
                    }
                },
                error: function(jqXHR, textStatus, errorThrown) {
                    iziToast.error({
                        title: 'Error',
                        message: 'Photo taking failed'
                    });
                }
            });
    
            // link.setAttribute("download", "photo");
            // link.classList.add("photo");
            // link.innerHTML = `<img src="${data}" alt="photo" />`;
            // // strip.insertBefore(link, strip.firstChild);
        }
    }).start()
};

const retakePhoto = () => {
    $('#take-check').hide();
    $('#take-photo').attr("disabled", false); // This just isn't working
    $('#take-photo').show();
    $('video-player').show();
    $('preview-photo').hide();
    video.play();
}

$(document).ready(function () {

    $('#take-wrap').hide();
    $('#filter-wrap').hide();
    
    $('#start-photo').click(function (e) {
        e.preventDefault();
        getVideo();
        $('#start-wrap').hide();
        $('#take-wrap').show();
	$('#preview-photo').hide();
        $('#take-check').hide();
    });

    $('#take-photo').click(function (e) {
        e.preventDefault();
        takePhoto();
        // Alternatively, call DSLR /capture api here
    });

    $('#retake-photo').click(retakePhoto);

    $('#confirm-photo').click(function (e) {
        e.preventDefault();
        // canvas.width = video.videoWidth;
        // canvas.height = video.videoHeight;
        canvas.width = previewCanvas.width;
        canvas.height = previewCanvas.height;
        ctx.drawImage(previewCanvas, 0, 0);
        currentFrame = canvas.toDataURL('image/jpeg', 1.0); // this is only temp, will be overwritten when we get low res from server
        iziToast.success({
            title: 'Photo Sent!',
            message: 'Please hold',
            timeout: 2000
        });
        $('#confirm-photo').attr("disabled", true); // This just isn't working
        // connect to backend
        $.ajax({
            type: "POST",
            url: requestFiltersUri,
            data: JSON.stringify({image: currentFrame}),    
            timeout: 30000,
            success: function (data, status) {
                console.log(data, status);
                if (status == "success") {
                    iziToast.info({
                        title: 'FYI',
                        message: 'Photo processed!'
                    });
                    $('#filter-wrap').show();
                    $('#take-wrap').hide();
                    
                    // Receive image data
                    const { filters, mask, source } = data; // source 
                    // console.log(mask);
                    // note mask is outline offset, copy
                    const normalMask = mask.map(maskRow => maskRow.map(e => e % OUTLINE_OFFSET));
                    var img = new Image();
                    img.onload = function(){
                        canvas.width = img.width;
                        canvas.height = img.height;
                        hoverCanvas.width = img.width;
                        hoverCanvas.height = img.height;
                        activeCanvas.width = img.width;
                        activeCanvas.height = img.height;
                        ctx.drawImage(img, 0, 0);
                    };
                    img.src = source;
                    // Load filters into imagedata
                    const srcData = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
                    // worried about some async bug here...
                    const flatMask = flatten(mask);
                    applyMask = applyMaskBase.bind(this, flatten(srcData), normalMask);
                    const trackMouseCanvas = trackMouseCanvasBase.bind(this, normalMask);
                    
                    Promise.all(filters.map((filterUri, index) => {
                        const url = `data:image/jpeg;base64,${filterUri}`;
                        const preview = document.getElementById(`preview-${index + 1}`);
                        preview.src = url;
                        return new Promise(resolve => {
                            // hack for getting image data, fetch isn't returning proper shape
                            var img = new Image();
                            img.onload = () => {
                                activeCtx.drawImage(img, 0, 0);
                                const filterSrc = activeCtx.getImageData(0, 0, canvas.width, canvas.height).data;                            
                                resolve(filterSrc);
                            };
                            img.src = url;
                            // return fetch(url)  // pass in some data-uri
                            // .then(function(response) {return response.arrayBuffer()})
                            // .then(function(buffer) {
                            //     return new Uint8Array(buffer);
                            // });
                        });
                    }))
                    .then((filterData) => {
                        activeCtx.clearRect(0, 0, canvas.width, canvas.height);
                        const flatFilters = filterData.map(im => flatten(im));
                        applyMask = applyMask.bind(this, flatFilters);
                    });
                    // const mask  BOOKMARK
                    const outlineMask = flatMask.map(el => el);// - OUTLINE_OFFSET);
                    applyActiveOutline = applyActiveOutlineBase.bind(this, outlineMask);
                    applyHoverOutline = applyHoverOutlineBase.bind(this, outlineMask);
        
                    $("#booth-photo").mousemove( event => {
                        mouseDict = getMousePos(event);
                        trackMouseCanvas(mouseDict);
                    });
                    $('#booth-photo').click( event => {
                        if (activeId != hoverId) {
                            activeId = hoverId;
                            applyActiveOutline();
                        } else {
                            activeId = -1;
                            activeCtx.clearRect(0, 0, activeCanvas.width, activeCanvas.height);
                        }
                        updateActiveFilter();
                    });
                } else {
                    iziToast.error({
                        title: 'Error',
                        message: 'Something went wrong'
                    });
                }
            },
            error: function(jqXHR, textStatus, errorThrown) {
                iziToast.error({
                    title: 'Error',
                    message: 'Something went wrong'
                });
            }
        });
    });

    // Filters
    $(".filter-option").click(e => {
        e.preventDefault();

        if (activeId === -1) {
            iziToast.info({
                title: 'FYI',
                message: 'Please select a part of the image!'
            });
            return;
        }
        // CSS handling
        const activeFilter = activeFilters[activeId];
        if (!e.target.dataset.filter) {
            console.error("filter-option does not have data-filter");
            console.log(e.target.dataset);
        }
        const filter = parseInt(e.target.dataset.filter.substr(6)); // trim 
        if (filter === activeFilter) { // currently active filter clicked again
            activeFilters[activeId] = "";
            e.target.classList.remove('active');
            applyMask();
        } else {
            if (!!activeFilter) {
                const activeNode = document.querySelector(
                    `[data-filter=filter${activeFilter}]`
                );
                activeNode ? activeNode.classList.remove('active') : null;
            }
            activeFilters[activeId] = filter;
            e.target.classList.add('active');
            applyMask(filter - 1);
        }
    });

    // Send

    $('#prompt-send').click(function (e) {
        $('#send-modal').modal();
    });
    

    $('#send-confirm').click(function (e) {
        // const url = canvas.toDataURL(); // TODO: make sure this is right
        const mixDict = activeFilters;
        for (entity in activeFilters) {
            activeFilters[entity] = activeFilters[entity] - 1; // stupid html offset
        }
        $.post(sendMessageUri, JSON.stringify({
            email: $('#email').val(),
            mixInfo: mixDict
        }), function (data, status) {
            console.log(data, status)
            if (status == 'success') {
                iziToast.success({
                    title: 'FYI',
                    message: 'Photo messaged!'
                });
                window.location.reload();
            } else {
                iziToast.error({
                    title: 'Error',
                    message: 'Something went wrong',
                    style: $('input[name=filter]:checked').val()
                });
            }
        });
    });

    $('.restart-button').click(() => {
        window.location.reload();
    });

    $('#booth-photo').mouseleave(() => {
        hoverId = -1;
        hoverCtx.clearRect(0, 0, hoverCanvas.width, hoverCanvas.height);
    })
});

const applyActiveOutlineBase = (maskData) => {
    if (!maskData) {
        console.error("Illegal call of applyActiveOutline");
        return;
    }
    activeCtx.clearRect(0, 0, activeCanvas.width, activeCanvas.height);
    const pixels = activeCtx.getImageData(0, 0, activeCanvas.width, activeCanvas.height);
    for (let i = 0; i < pixels.data.length / 4; i += 1) {
        pixelIndex = 4 * i;
        if (maskData[i] == activeId) {
            // TODO: better colors
            pixels.data[pixelIndex + 0] = 0;
            pixels.data[pixelIndex + 1] = 0;
            pixels.data[pixelIndex + 2] = 255;
            pixels.data[pixelIndex + 3] = 255;
        }
    }
    activeCtx.putImageData(pixels, 0, 0);
}

const applyHoverOutlineBase = (maskData) => {
    if (!maskData) {
        console.error("Illegal call of applyHoverOutline");
        return;
    }

    hoverCtx.clearRect(0, 0, hoverCanvas.width, hoverCanvas.height);
    const pixels = hoverCtx.getImageData(0, 0, hoverCanvas.width, hoverCanvas.height);
    for (let i = 0; i < pixels.data.length / 4; i += 1) {
        pixelIndex = 4 * i;
        if (maskData[i] == hoverId) {
            // TODO: get some better colors in here dear god
            pixels.data[pixelIndex + 0] = 255;
            pixels.data[pixelIndex + 1] = 0;
            pixels.data[pixelIndex + 2] = 0;
            pixels.data[pixelIndex + 3] = 255;
        } else {
            pixels.data[pixelIndex + 3] = 0;
        }
    }
    hoverCtx.putImageData(pixels, 0, 0);
}

// Request data flattened
// Note this must reference activeID TODO
const applyMaskBase = (baseData, maskData, filterData, filter) => {
    if (!baseData || !maskData || !filterData) { // TODO: verify shape of data too
        console.error("Illegal call of applyMask");
        return;
    }
    const pixels = ctx.getImageData(0, 0, canvas.width, canvas.height);
    
    const filterSource = (filter !== undefined) ? filterData[filter] : baseData;
    // console.log(baseData.length);
    // console.log(filterSource.length);
    // console.log(filter);

    for (let i = 0; i < pixels.data.length / 4; i += 1) {
        // For each pixel
        // If outlines, apply set colors
        pixelIndex = 4 * i;
        if (maskData[i] == activeId) { // TODO: sub in actual filters
            pixelIndex = 4 * i;
            pixels.data[pixelIndex + 0] = filterSource[pixelIndex + 0];
            pixels.data[pixelIndex + 1] = filterSource[pixelIndex + 1];
            pixels.data[pixelIndex + 2] = filterSource[pixelIndex + 2];
        }
    }
    ctx.putImageData(pixels, 0, 0);
};
// video.addEventListener("canplay", paintToCanvas);

// This function makes sure the right option is shown to be active
const updateActiveFilter = () => {
    filterOption = document.querySelector('.filter-option.active');
    if (activeId === -1) {
        // disable current active and exit
        if (filterOption)
            filterOption.classList.remove('active');
        return;   
    }
    console.log(filterOption);
    const activeFilter = activeFilters[activeId];
    if (filterOption) {
        console.log('updating active filter, id then filter:', activeId, activeFilter);
        if (parseInt(filterOption.dataset.filter) != activeFilter) {
            filterOption.classList.remove('active');
        } else return;
    }
    // add new active
    if (activeFilter) {
        const newActive = document.querySelector(
            `[data-filter=filter${activeFilter}]`
        );
        newActive.classList.add('active');
    }
}

// Sets hovered ID/tracks outline
const trackMouseCanvasBase = (maskData, mouseDict) => {
    if (!maskData) return;
    shouldUpdate = hoverId != maskData[mouseDict.y][mouseDict.x];
    hoverId = maskData[mouseDict.y][mouseDict.x];
    if (shouldUpdate)
        applyHoverOutline();
}

// Some util below
/* Track mouse and deal with outlines and updating hover piece */
// Get mouse position in canvas, rounded
function getMousePos(evt) {
    var rect = canvas.getBoundingClientRect();
    return {
        x: Math.round((evt.clientX - rect.left) / (rect.right - rect.left) * canvas.width),
        y: Math.round((evt.clientY - rect.top) / (rect.bottom - rect.top) * canvas.height)
    };
}

const flatten = function(arr, result = []) {
    for (let i = 0, length = arr.length; i < length; i++) {
        const value = arr[i];
        if (Array.isArray(value)) {
        flatten(value, result);
        } else {
        result.push(value);
        }
    }
    return result;
};

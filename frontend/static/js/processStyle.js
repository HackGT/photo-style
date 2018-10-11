var filter = document.getElementById('filter');

$.get("http://128.61.105.52/styles", function (data, status) {
    console.log(data,status);
    if(status !== 'success') {
        return iziToast.error({
                title: 'Error',
                message: 'Could not retrieve styles'
            });
    }

    for(var i = 0; i < data.styles.length; i++) {
        // <input type="radio" name="Filter" value="filter-1">
        // <label for="filter-1">
        //     <img src="./assets/images/placeholder.png" alt="">
        // </label>
        var div = document.createElement('div');
        var input = document.createElement('input');
        input.type = 'radio';
        input.name = 'filter';
        input.value = data.styles[i];
        input.id = data.styles[i];
        var label = document.createElement('label');
        label.setAttribute('for', data.styles[i]);
        var image = document.createElement('img');
        image.src = './assets/images/' + data.styles[i] + '.png';
        image.onerror = function(err) {
            this.src = './assets/images/placeholder.png';
        }
        image.width = 150;
        image.alt = data.styles[i];
        label.innerText=data.styles[i];
        label.appendChild(image);
        div.appendChild(input);
        div.appendChild(label);
        filter.appendChild(div);
    }
});

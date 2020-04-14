$(function () {

    $("#file-upload").change(function () {
        console.log('about to upload data from' + this.files[0].name);
        var reader = new FileReader();
        reader.readAsText(this.files[0], 'UTF-8')
        reader.onload = shipOff
    })

    function shipOff(event) {
        console.log('Post upload request');
        var result = event.target.result
        var data = { data: result, objtype: upload_type }
        $.post('upload', JSON.stringify(data), function (resp, status) {
            let answer = JSON.parse(resp)
            alert(answer.msg)
            location.reload()
        })
    }
})

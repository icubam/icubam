function formatColumn (column) {
  let result = {data: column}
  result.render = function (data, type, full, meta) {
    // This is kind of a hack. We print both value and sorted_value separted
    // by two colons and use them to split the display value from the sorted
    // one.
    if (data.includes('::')) {
      parts = data.split('::')      
      if(type == 'display') {
        return parts[0]
      } else {
        return parts[1]
      }
    } else {
      return data
    }
  }
  return result
}


function setDatatable (table_id, columns) {
  let table = $(table_id).DataTable({
    responsive: true,
    autoWidth: false,
    columns: columns.map(x => formatColumn(x))
  })
}

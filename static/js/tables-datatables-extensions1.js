/**
 * DataTables Extensions (jquery)
 */

'use strict';

$(function () {
  var dt_scrollable_table = $('.dt-scrollableTable'),
    dt_fixedheader_table = $('.dt-fixedheader'),
    dt_fixedcolumns_table = $('.dt-fixedcolumns'),
    dt_select_table = $('.dt-select-table');

  // FixedHeader
  // --------------------------------------------------------------------

  if (dt_fixedheader_table.length) {
    var dt_fixedheader = dt_fixedheader_table.DataTable({
      ajax: assetsPath + 'json/table-datatable1.json',
      columns: [
        { data: '' },
        { data: 'id' },
        { data: 'id' },
        { data: 'date' },
        { data: 'customer' },
        { data: 'manager' },
        { data: 'quantity' },
        { data: 'weight' },
        { data: 'status' },
        { data: '' },
      ],
      columnDefs: [
        {
          className: 'control',
          orderable: false,
          targets: 0,
          responsivePriority: 3,
          render: function (data, type, full, meta) {
            return '';
          }
        },
        {
          // For Checkboxes
          targets: 1,
          orderable: false,
          render: function () {
            return '<input type="checkbox" class="dt-checkboxes form-check-input">';
          },
          checkboxes: {
            selectAllRender: '<input type="checkbox" class="form-check-input">'
          },
          responsivePriority: 2
        },
        {
          responsivePriority: 2,
          targets: 2,
          visible: true
        },
        {
          responsivePriority: 1,
          targets: 3,
          visible: true
        },
        {
          // customer Avatar image/badge, Name and email
          targets: 4,
          render: function(data, type, full, meta) {
            var $name = full['customer'],
                $email = full['customer_email'];

            var $row_output =
                '<div class="d-flex justify-content-start align-items-center">' +
                '<div class="d-flex flex-column">' +
                '<span class="emp_name text-truncate text-heading fw-medium">' +
                $name +
                '</span>' +
                '<small class="emp_email text-truncate">' +
                $email +
                '</small>' +
                '</div>' +
                '</div>';
            return $row_output;
          },
          responsivePriority: 1
        },
        {
          // manager Avatar image/badge, Name and email
          targets: 5,
          render: function(data, type, full, meta) {
            var $name = full['manager'],
                $email = full['manager_email'];

            var $row_output =
                '<div class="d-flex justify-content-start align-items-center">' +
                '<div class="d-flex flex-column">' +
                '<span class="emp_name text-truncate text-heading fw-medium">' +
                $name +
                '</span>' +
                '<small class="emp_email text-truncate">' +
                $email +
                '</small>' +
                '</div>' +
                '</div>';
            return $row_output;
          },
          responsivePriority: 1
        },
        {
          responsivePriority: 1,
          targets: 6
        },
        {
          responsivePriority: 1,
          targets: 7
        },
        {
          responsivePriority: 1,
          targets: 8
        },
        {
          responsivePriority: 1,
          targets: 9
        },

        {
          // Label
          targets: -2,
          render: function (data, type, full, meta) {
            // var $rand_num = Math.floor(Math.random() * 5) + 1;
            var $status_number = full['status'];
            var $status = {
              1: { title: 'Принят на склад', class: 'bg-label-primary' },
              2: { title: 'На отправку', class: ' bg-label-success' },
              3: { title: 'Отклонен', class: ' bg-label-danger' },
              4: { title: 'Не определен', class: ' bg-label-warning' },
              5: { title: 'Applied', class: ' bg-label-info' }
            };
            if (typeof $status[$status_number] === 'undefined') {
              return data;
            }
            return (
              '<span class="badge rounded-pill ' +
              $status[$status_number].class +
              '">' +
              $status[$status_number].title +
              '</span>'
            );
          }
        },
        {
          // Actions
          targets: -1,
          title: 'Действие',
          orderable: false,
          render: function (data, type, full, meta) {
            return (
              '<div class="d-inline-block">' +
              '<a href="javascript:;" class="btn btn-sm btn-text-secondary rounded-pill btn-icon dropdown-toggle hide-arrow" data-bs-toggle="dropdown"><i class="mdi mdi-dots-vertical"></i></a>' +
              '<div class="dropdown-menu dropdown-menu-end m-0">' +
              '<a href="javascript:;" class="dropdown-item">Детали</a>' +
              '<a href="javascript:;" class="dropdown-item">Действие</a>' +
              '<div class="dropdown-divider"></div>' +
              '<a href="javascript:;" class="dropdown-item text-danger delete-record">Удалить</a>' +
              '</div>' +
              '</div>' +
              '<a href="javascript:;" class="btn btn-sm btn-text-secondary rounded-pill btn-icon item-edit"><i class="mdi mdi-pencil-outline"></i></a>'
            );
          }
        }
      ],
      order: [[2, 'desc']],
      dom: '<"row"<"col-sm-12 col-md-6"l><"col-sm-12 col-md-6 d-flex justify-content-center justify-content-md-end"f>>t<"row"<"col-sm-12 col-md-6"i><"col-sm-12 col-md-6"p>>',
      displayLength: 25,
      lengthMenu: [7, 10, 25, 50, 75, 100],
      responsive: {
        details: {
          display: $.fn.dataTable.Responsive.display.modal({
            header: function (row) {
              var data = row.data();
              return 'Details of incoming #' + data['id'];
            }
          }),
          type: 'column',
          renderer: function (api, rowIdx, columns) {
            var data = $.map(columns, function (col, i) {
              return col.title !== '' // ? Do not show row in modal popup if title is blank (for check box)
                ? '<tr data-dt-row="' +
                    col.rowIndex +
                    '" data-dt-column="' +
                    col.columnIndex +
                    '">' +
                    '<td>' +
                    col.title +
                    ':' +
                    '</td> ' +
                    '<td>' +
                    col.data +
                    '</td>' +
                    '</tr>'
                : '';
            }).join('');

            return data ? $('<table class="table"/><tbody />').append(data) : false;
          }
        }
      }
    });
    // Fixed header
    if (window.Helpers.isNavbarFixed()) {
      var navHeight = $('#layout-navbar').outerHeight();
      new $.fn.dataTable.FixedHeader(dt_fixedheader).headerOffset(navHeight);
    } else {
      new $.fn.dataTable.FixedHeader(dt_fixedheader);
    }
  }
});

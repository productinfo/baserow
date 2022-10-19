<template>
  <div>
    <div class="data-table">
      <div class="data-table__header">
        <h1 class="data-table__title">12 Members in ACME Corp</h1>
        <div class="data-table__actions">
          <div class="input__with-icon input__with-icon--left">
            <input
              type="text"
              placeholder="Find member..."
              class="input input--large"
            />
            <i class="fas fa-search"></i>
          </div>
          <a href="#" class="button button--large margin-left-2"
            >Invite member</a
          >
        </div>
      </div>
      <div class="data-table__body">
        <table class="data-table__table">
          <thead>
            <tr class="data-table__table-row">
              <th
                class="
                  data-table__table-cell
                  data-table__table-cell--sticky-left
                  data-table__table-cell--header
                "
              >
                <div class="data-table__table-cell-head">
                  <Checkbox v-model="c" class="checkbox--small"></Checkbox>
                </div>
              </th>
              <th class="data-table__table-cell data-table__table-cell--header">
                <div class="data-table__table-cell-head">
                  <a href="#" class="data-table__table-cell-head-link">Name</a>
                  <div>
                    <i class="fas fa-sort-down"></i>
                    0
                  </div>
                </div>
              </th>
              <th class="data-table__table-cell data-table__table-cell--header">
                <div class="data-table__table-cell-head">Email</div>
              </th>
              <th class="data-table__table-cell data-table__table-cell--header">
                <div class="data-table__table-cell-head">
                  Workspace permissions
                  <div>
                    <i class="fas fa-sort-up"></i>
                    1
                  </div>
                </div>
              </th>
              <th class="data-table__table-cell data-table__table-cell--header">
                <div class="data-table__table-cell-head">Team</div>
              </th>
              <th
                class="
                  data-table__table-cell
                  data-table__table-cell--header
                  data-table__table-cell--sticky-right
                "
              >
                <div class="data-table__table-cell-head"></div>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(i, i2) in new Array(10)"
              :key="i2"
              class="data-table__table-row"
              :class="{
                'data-table__table-row--selected': i2 === 2,
                'data-table__table-row--hover': i2 === 4,
              }"
            >
              <td
                class="
                  data-table__table-cell data-table__table-cell--sticky-left
                "
              >
                <div class="data-table__table-cell-content">
                  <Checkbox v-model="c" class="checkbox--small"></Checkbox>
                </div>
              </td>
              <td class="data-table__table-cell">
                <div class="data-table__table-cell-content">
                  This is a very long name that doesn't completely fit.
                </div>
              </td>
              <td class="data-table__table-cell">
                <div class="data-table__table-cell-content">
                  This is a very long name that doesn't completely fit.
                </div>
              </td>
              <td class="data-table__table-cell">
                <div class="data-table__table-cell-content">
                  This is a very long name that doesn't completely fit.
                </div>
              </td>
              <td class="data-table__table-cell">
                <div class="data-table__table-cell-content">
                  This is a very long name that doesn't completely fit.
                </div>
              </td>
              <td
                class="
                  data-table__table-cell data-table__table-cell--sticky-right
                "
              >
                <div class="data-table__table-cell-content">
                  <a href="#" class="data-table__more">
                    <i class="fas fa-ellipsis-h"></i>
                  </a>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="data-table__footer">
        <div class="paginator">
          <div class="paginator__name">page</div>
          <div class="paginator__group">
            <a class="paginator__button paginator__button--disabled"
              ><i class="fas fa-caret-left"></i
            ></a>
            <input
              type="number"
              class="input paginator__page-input"
              value="1"
            />
            <div class="paginator__count">of 233</div>
            <a class="paginator__button"><i class="fas fa-caret-right"></i></a>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'DataTable',
  data() {
    return {
      c: false,
    }
  },
}
</script>

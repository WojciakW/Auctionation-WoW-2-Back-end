const createCsvWriter = require('csv-writer').createObjectCsvWriter;
const Database = require('wow-classic-items');

const csvWriter = createCsvWriter({
    path: 'out.csv',
    header: [
        {id: 'id',          title: 'id'},
        {id: 'name',        title: 'name'},
        {id: 'class',       title: 'class'},
        {id: 'subclass',    title: 'subclass'},
        {id: 'slot',        title: 'slot'},
        {id: 'quality',     title: 'quality'},
        {id: 'icon_url',    title: 'icon_url'}
    ]
});

const items = new Database.Items();

let data = [];

for (const item of items) {
    data.push(
        {
            id:         `${item.itemId}`,
            name:       `${item.name}`,
            class:      `${item.class}`,
            subclass:   `${item.subclass}`,
            slot:       `${item.slot}`,
            quality:    `${item.quality}`,
            icon_url:   `${item.icon}`
        }
    )
}

csvWriter
    .writeRecords(data)
    .then(() => console.log('Data written.'))
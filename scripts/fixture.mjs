// node scripts/fixture.mjs > tests/fixtures/order-link.txt   (the sample menu as an order-link fragment)
import { encodeMenu, SAMPLE } from "../site/assets/order-core.js";
console.log(await encodeMenu(SAMPLE));

// Pricing logic for the Sandfontein web calculator.
// Mirrors rate-calculator/calculator.py; keep the two in step.
(function (root) {
  "use strict";

  function parseDate(iso) {
    var p = iso.split("-").map(Number);
    return new Date(Date.UTC(p[0], p[1] - 1, p[2]));
  }

  function round2(x) {
    return Math.round(x * 100) / 100;
  }

  function bookingDiscount(nights, repeatGuest, rates) {
    var rate = 0, reasons = [];
    if (nights >= rates.long_stay_nights) {
      rate += rates.long_stay_discount;
      reasons.push(Math.round(rates.long_stay_discount * 100) + "% for " + rates.long_stay_nights + "+ nights");
    }
    if (repeatGuest) {
      rate += rates.repeat_guest_discount;
      reasons.push(Math.round(rates.repeat_guest_discount * 100) + "% repeat guest");
    }
    return { rate: Math.round(rate * 10000) / 10000, reasons: reasons };
  }

  // Throws an Error with a guest-friendly message for invalid input.
  function quote(opts, rates) {
    var adults = opts.adults, children = opts.children, babies = opts.babies;
    var card = rates.rate_cards[opts.rateCard];
    var max = rates.max_guests;
    if (!card) throw new Error("Unknown rate card.");
    if ([adults, children, babies].some(function (n) { return !Number.isInteger(n) || n < 0; }))
      throw new Error("Guest numbers must be whole numbers, zero or more.");
    if (adults < 1) throw new Error("At least one adult is required.");
    if (adults + children > max) throw new Error("Sandfontein sleeps at most " + max + " paying guests.");
    if (!opts.checkIn || !opts.checkOut) throw new Error("Choose check-in and check-out dates.");

    var checkIn = parseDate(opts.checkIn), checkOut = parseDate(opts.checkOut);
    if (checkOut <= checkIn) throw new Error("Check-out must be after check-in.");

    var nights = [];
    for (var d = new Date(checkIn); d < checkOut; d.setUTCDate(d.getUTCDate() + 1)) nights.push(new Date(d));
    var highNights = nights.filter(function (n) {
      return rates.high_season_months.indexOf(n.getUTCMonth() + 1) !== -1;
    }).length;
    var lowNights = nights.length - highNights;

    var warnings = [];
    if (nights.some(function (n) { return n.getUTCFullYear() !== rates.year; }))
      warnings.push("Some nights fall outside " + rates.year + "; " + rates.year + " rates have been used for them.");
    if (adults + children + babies > max)
      warnings.push("The party (including babies) is larger than the " + max + " beds available.");

    var discount = bookingDiscount(nights.length, opts.repeatGuest, rates);
    var lines = [], counts = { Adult: 0, Child: 0 };
    var party = [];
    for (var a = 0; a < adults; a++) party.push(["Adult", 1]);
    for (var c = 0; c < children; c++) party.push(["Child", 1 - rates.child_discount]);

    party.forEach(function (g, i) {
      var type = g[0], factor = g[1];
      counts[type] += 1;
      var high = card.high[i] * factor, low = card.low[i] * factor;
      var subtotal = round2(high * highNights + low * lowNights);
      var disc = round2(subtotal * discount.rate);
      lines.push({ label: type + " " + counts[type], type: type, position: i + 1,
                   highRate: high, lowRate: low, subtotal: subtotal, discount: disc,
                   total: round2(subtotal - disc) });
    });
    for (var b = 1; b <= babies; b++)
      lines.push({ label: "Baby " + b, type: "Baby", position: null, highRate: 0, lowRate: 0,
                   subtotal: 0, discount: 0, total: 0 });

    function sum(key) {
      return round2(lines.reduce(function (s, l) { return s + l[key]; }, 0));
    }
    return {
      currency: card.currency, nights: nights.length, highNights: highNights, lowNights: lowNights,
      discountRate: discount.rate, discountReasons: discount.reasons, lines: lines,
      subtotal: sum("subtotal"), discount: sum("discount"), total: sum("total"),
      // Grand total per paying guest (adults + children) per night.
      avgPerPersonNight: round2(sum("total") / ((adults + children) * nights.length)),
      warnings: warnings,
    };
  }

  var api = { quote: quote };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.SandfonteinCalculator = api;
})(this);

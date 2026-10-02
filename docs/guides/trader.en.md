# Trader guide

You represent an organisation of a West African Power Pool country on the day-ahead market. You submit sell and buy orders for each hour, the trainer runs the clearing, and you discover what was accepted, at what price, and what you earned.

## 1. Entering the room

From the hall, enter the code given by the trainer, your organisation and your zone. The name must be unique in the room. If you pick a suggested name, you take the place of the matching real actor in the background data (its plants or demand disappear, yours replace them). With a free name, your orders are added to the existing market.

## 2. Submitting orders

The order book has four tabs. "Save" replaces all your orders with what is on screen; you can edit until submission closes.

**Sell.** One row per segment: plant name, segment number (0 to 3, increasing prices for the same asset), quantity in MW, price per MWh, hourly profile. The profile shapes the available quantity hour by hour: *baseload* 95% all day, *hydro* between 60 and 100%, *solar* zero at night and maximal at noon, *peaker* and *flat* 100%. A segment can be partially accepted.

**Buy.** Same logic: load name, quantity at peak, maximum price you accept to pay. The quantity follows the West African load profile automatically (night trough, evening peak).

**Blocks.** A block is accepted in full over all its hours, or rejected: useful for a plant that cannot start for two hours, or a continuous industrial load. A *child* block is accepted only if its *parent* is (give the parent's name). In an *exclusive group* (same group label), at most one option is selected.

**MIC.** Minimum income condition for a seller: if your revenue at final prices is below the fixed term plus the variable term times the accepted volume, all your orders are withdrawn and the market is recomputed without you.

## 3. Understanding the result

- Each country gets a **price per hour**. A sell order is accepted if its price is at or below the zonal price, a buy order if its price is at or above. The order priced exactly at the zonal price may be only partially accepted.
- Without congestion, two connected countries have the **same price**. When a line is saturated, the importing country is more expensive: visible on the map, line in red.
- A **block** can be rejected although it would have been profitable at final prices: accepting it would have changed everyone's prices and reduced total value. This paradoxical rejection is normal in this kind of market. A block is never accepted at a loss.
- You are paid or you pay at **your zone's price**, not at your offer price: your surplus is the difference.

## 4. Reading "My result"

Sold and bought (accepted over offered), surplus, number of rejected orders, detail per asset with the average price obtained, status of your blocks, hourly prices of your zone. Results arrive live as soon as the trainer runs the clearing.

## 5. Tips

- Offer your plants at their **variable cost**: above it you risk rejection, below it you risk selling at a loss.
- Split a plant into segments of increasing price rather than a single price block.
- Use a block only when the all-or-nothing constraint is real: it can cost you a sale a segment would have won.
- Watch saturated lines: a country isolated by congestion sets its own price.

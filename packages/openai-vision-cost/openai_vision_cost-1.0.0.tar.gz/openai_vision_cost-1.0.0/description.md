# Calculating costs

Image inputs are metered and charged in tokens, just as text inputs are. How images are converted to text token inputs varies based on the model. You can find a vision pricing calculator in the FAQ section of the [pricing page](https://openai.com/api/pricing/).

## GPT-4.1-mini, GPT-4.1-nano, o4-mini

Image inputs are metered and charged in tokens based on their dimensions. The token cost of an image is determined as follows:

- Calculate the number of 32px x 32px patches that are needed to fully cover the image
- If the number of patches exceeds 1536, we scale down the image so that it can be covered by no more than 1536 patches
- The token cost is the number of patches, capped at a maximum of 1536 tokens
- For `gpt-4.1-mini` we multiply image tokens by 1.62 to get total tokens, for `gpt-4.1-nano` we multiply image tokens by 2.46 to get total tokens, and for `o4-mini` we multiply image tokens by 1.72 to get total tokens, that are then billed at normal text token rates.

**Cost calculation examples**

- A 1024 x 1024 image is **1024 tokens**
  - Width is 1024, resulting in `(1024 + 32 - 1) // 32 = 32` patches
  - Height is 1024, resulting in `(1024 + 32 - 1) // 32 = 32` patches
  - Tokens calculated as `32 * 32 = 1024`, below the cap of 1536

- A 1800 x 2400 image is **1452 tokens**
  - Width is 1800, resulting in `(1800 + 32 - 1) // 32 = 57` patches
  - Height is 2400, resulting in `(2400 + 32 - 1) // 32 = 75` patches
  - We need `57 * 75 = 4275` patches to cover the full image. Since that exceeds 1536, we need to scale down the image while preserving the aspect ratio.
  - We can calculate the shrink factor as `sqrt(token_budget × patch_size^2 / (width * height))`. In our example, the shrink factor is `sqrt(1536 * 32^2 / (1800 * 2400)) = 0.603`.
  - Width is now 1086, resulting in `1086 / 32 = 33.94` patches
  - Height is now 1448, resulting in `1448 / 32 = 45.25` patches
  - We want to make sure the image fits in a whole number of patches. In this case we scale again by `33 / 33.94 = 0.97` to fit the width in 33 patches.
  - The final width is then `1086 * (33 / 33.94) = 1056)` and the final height is `1448 * (33 / 33.94) = 1408`
  - The image now requires `1056 / 32 = 33` patches to cover the width and `1408 / 32 = 44` patches to cover the height
  - The total number of tokens is the `33 * 44 = 1452`, below the cap of 1536

## GPT 4o, GPT-4.1, GPT-4o-mini, CUA, and o-series (except o4-mini)

The token cost of an image is determined by two factors: size and detail.

Any image with `"detail": "low"` costs a set, base number of tokens. This amount varies by model (see chart below). To calculate the cost of an image with `"detail": "high"`, we do the following:

- Scale to fit in a 2048px x 2048px square, maintaining original aspect ratio
- Scale so that the image's shortest side is 768px long
- Count the number of 512px squares in the image—each square costs a set amount of tokens (see chart below)
- Add the base tokens to the total

| Model | Base tokens | Tile tokens |
|-------|-------------|-------------|
| 4o, 4.1, 4.5 | 85 | 170 |
| 4o-mini | 2833 | 5667 |
| o1, o1-pro, o3 | 75 | 150 |
| computer-use-preview | 65 | 129 |

**Cost calculation examples (for gpt-4o)**

- A 1024 x 1024 square image in `"detail": "high"` mode costs 765 tokens
  - 1024 is less than 2048, so there is no initial resize.
  - The shortest side is 1024, so we scale the image down to 768 x 768.
  - 4 512px square tiles are needed to represent the image, so the final token cost is `170 * 4 + 85 = 765`.

- A 2048 x 4096 image in `"detail": "high"` mode costs 1105 tokens
  - We scale down the image to 1024 x 2048 to fit within the 2048 square.
  - The shortest side is 1024, so we further scale down to 768 x 1536.
  - 6 512px tiles are needed, so the final token cost is `170 * 6 + 85 = 1105`.

- A 4096 x 8192 image in `"detail": "low"` most costs 85 tokens
  - Regardless of input size, low detail images are a fixed cost.

## GPT Image 1

For GPT Image 1, we calculate the cost of an image input the same way as described above, except that we scale down the image so that the shortest side is 512px instead of 768px.
There is no detail level configuration for this model, so the price depends on the dimensions of the image.

The base cost is 65 image tokens, and each tile costs 129 image tokens.

To see pricing for image input tokens, refer to our [pricing page](/docs/pricing#latest-models).

---

We process images at the token level, so each image we process counts towards your tokens per minute (TPM) limit.

For the most precise and up-to-date estimates for image processing, please use our image pricing calculator available [here](https://openai.com/api/pricing/).
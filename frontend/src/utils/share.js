export function generateShareLink(network, url, title = "") {
  const encodedUrl = encodeURIComponent(url);
  const encodedTitle = encodeURIComponent(title);

  switch (network) {
    case "vk":
      return `https://vk.com/share.php?url=${encodedUrl}&title=${encodedTitle}`;
    case "telegram":
      return `https://t.me/share/url?url=${encodedUrl}&text=${encodedTitle}`;
    case "twitter":
      return `https://twitter.com/intent/tweet?url=${encodedUrl}&text=${encodedTitle}`;
    default:
      return "#";
  }
}

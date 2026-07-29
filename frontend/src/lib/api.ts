import { economics, reviews, traceEvents } from "./mockData";

export async function getReviews() {
  return reviews;
}

export async function getReview(id: string) {
  return reviews.find((review) => review.id === id) ?? reviews[0];
}

export async function getTrace() {
  return traceEvents;
}

export async function getEconomics() {
  return economics;
}


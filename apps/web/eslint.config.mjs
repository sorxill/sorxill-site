// eslint-config-next 16 экспортирует готовый flat-массив дефолтом.
import next from "eslint-config-next";

const config = [
  ...next,
  { ignores: [".next/**", "node_modules/**", "next-env.d.ts"] },
];

export default config;

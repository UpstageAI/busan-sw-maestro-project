import { createGlobalStyle } from "styled-components";
import { theme } from "./theme";

const GlobalStyle = createGlobalStyle`
    * { box-sizing: border-box; }

    body {
        margin: 0;
        background: ${theme.paper};
        color: ${theme.ink};
        font-family: 'Pretendard', system-ui, sans-serif;
        font-size: 14px;
        line-height: 1.5;
        -webkit-font-smoothing: antialiased;
        background-image: radial-gradient(${theme.hair} 0.6px, transparent 0.6px);
        background-size: 22px 22px;
    }
`;

export default GlobalStyle;

import ast
import logging
from src.client.llm_client import LLMClient
from src.repos.champions_repo import ImageDict

logger = logging.getLogger("TeamSuggestionUseCase")


class TeamSuggestionUseCase:
    def __init__(self, llm_client: LLMClient, champion_data: ImageDict) -> None:
        self._llmc_lient = llm_client
        self._champion_data = champion_data
        pass


    def suggest_team(self, team_size: int, champions_ids: list[str]) -> list[str]:
        champions_names = [self._champion_data[_id]["name"] for _id in champions_ids]
        prompt = f"""
            dado o seguinte conjunto de campeões: {",".join(champions_names)} me sugira um time com {team_size}
            campeões ótimo para uma partida no mapa Howling Abyss em League of Legends, prezando o equilibrio
            de dano mágico e físico dos campeões e que cada time tenha uma boa distribuição de suporte,
            dano e tanque.
            me responda apenas com lista de strings com os nomes dos campeões nesse formato:
            ["Campeao1","Campeao2","Campeao3"]
        """

        try:
            llm_return = self._llmc_lient.generate_text(prompt).content
        except Exception as e:
            logger.error(f"failed to call llm model: {e}")
            raise e

        try:
            suggested_team = ast.literal_eval(llm_return)
            return suggested_team
        except Exception as e:
            logger.error(f"failed to parse llm response: {e}")
            raise e


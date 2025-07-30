import { LabIcon } from '@jupyterlab/ui-components';
import ConnectorSingleton from '../../connection/connectorSingleton';
import { userIcon } from '../LabIcons';

let userSVG: LabIcon | HTMLImageElement;
const getProfile = async () => {
  if (userSVG) {
    return userSVG;
  }
  const config = ConnectorSingleton.getInstance();
  let user;
  try {
    user = (await config.userApi.userSnapshot()).user;
  } catch (e) {
    //
  }

  const profilePic = user?.picture;

  if (profilePic) {
    const img = new Image();
    img.src = profilePic;
    userSVG = img;
  } else {
    userSVG = userIcon;
  }
  return userSVG;
};

export default getProfile;
